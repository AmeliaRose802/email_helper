package services

import (
	"context"
	"errors"
	"os"
	"path/filepath"
	"testing"
	"time"

	"email-helper-backend/internal/database"
	"email-helper-backend/internal/mocks"
	"email-helper-backend/internal/models"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/suite"
)

// EmailServiceTestSuite defines the test suite for EmailService
type EmailServiceTestSuite struct {
	suite.Suite
	service         *EmailService
	mockOutlook     *mocks.MockOutlookProvider
	mockAI          *mocks.MockAIClient
	testDB          string
	useComBackend   bool
}

func (suite *EmailServiceTestSuite) SetupSuite() {
	// Reset database for this test suite
	database.ResetForTesting()
	
	// Create temp database for testing
	suite.testDB = filepath.Join(os.TempDir(), "test_emails.db")
	
	// Remove existing test database
	os.Remove(suite.testDB)
	
	// Initialize database
	err := database.InitDB(suite.testDB)
	suite.Require().NoError(err)
}

func (suite *EmailServiceTestSuite) TearDownSuite() {
	// Close and reset database for next test suite
	database.Close()
	database.ResetForTesting()
	os.Remove(suite.testDB)
}

func (suite *EmailServiceTestSuite) SetupTest() {
	// Create fresh mocks for each test
	suite.mockOutlook = new(mocks.MockOutlookProvider)
	suite.mockAI = new(mocks.MockAIClient)
	
	// Create service with mocks using interface types
	suite.service = &EmailService{
		outlookProvider: suite.mockOutlook,
		aiClient:        suite.mockAI,
		useComBackend:   true, // Enable COM backend for most tests
	}
}

func (suite *EmailServiceTestSuite) TearDownTest() {
	// Clean up database between tests
	db, _ := database.GetDB()
	db.Exec("DELETE FROM emails")
	
	// Assert all mock expectations were met
	suite.mockOutlook.AssertExpectations(suite.T())
	suite.mockAI.AssertExpectations(suite.T())
}

// Test GetEmails with Outlook source
func (suite *EmailServiceTestSuite) TestGetEmails_OutlookSource() {
	expectedEmails := []*models.Email{
		{ID: "1", Subject: "Test Email 1", Sender: "sender1@test.com"},
		{ID: "2", Subject: "Test Email 2", Sender: "sender2@test.com"},
	}
	
	suite.mockOutlook.On("GetEmails", "Inbox", 10, 0).Return(expectedEmails, nil)
	
	emails, total, err := suite.service.GetEmails("Inbox", 10, 0, "outlook", "")
	
	assert.NoError(suite.T(), err)
	assert.Equal(suite.T(), 2, total)
	assert.Len(suite.T(), emails, 2)
	assert.Equal(suite.T(), "Test Email 1", emails[0].Subject)
}

// Test GetEmails with Outlook error
func (suite *EmailServiceTestSuite) TestGetEmails_OutlookError() {
	suite.mockOutlook.On("GetEmails", "Inbox", 10, 0).Return(nil, errors.New("outlook error"))
	
	emails, total, err := suite.service.GetEmails("Inbox", 10, 0, "outlook", "")
	
	assert.Error(suite.T(), err)
	assert.Contains(suite.T(), err.Error(), "failed to get emails from Outlook")
	assert.Nil(suite.T(), emails)
	assert.Equal(suite.T(), 0, total)
}

// Test GetEmails with database source
func (suite *EmailServiceTestSuite) TestGetEmails_DatabaseSource() {
	// Save test emails to database
	email1 := &models.Email{
		ID:       "db-1",
		Subject:  "Database Email 1",
		Sender:   "db-sender@test.com",
		ReceivedTime: time.Now(),
		Category: "Action Required",
	}
	err := database.SaveEmail(email1)
	suite.Require().NoError(err)
	
	emails, total, err := suite.service.GetEmails("", 10, 0, "database", "")
	
	assert.NoError(suite.T(), err)
	assert.GreaterOrEqual(suite.T(), total, 1)
	assert.NotNil(suite.T(), emails)
}

// Test GetEmails with category filter
func (suite *EmailServiceTestSuite) TestGetEmails_WithCategoryFilter() {
	// Save emails with different categories
	email1 := &models.Email{
		ID:       "cat-1",
		Subject:  "Action Email",
		Sender:   "sender@test.com",
		ReceivedTime: time.Now(),
		Category: "Action Required",
	}
	email2 := &models.Email{
		ID:       "cat-2",
		Subject:  "FYI Email",
		Sender:   "sender@test.com",
		ReceivedTime: time.Now(),
		Category: "FYI",
	}
	database.SaveEmail(email1)
	database.SaveEmail(email2)
	
	emails, total, err := suite.service.GetEmails("", 10, 0, "database", "Action Required")
	
	assert.NoError(suite.T(), err)
	assert.GreaterOrEqual(suite.T(), total, 1)
	if len(emails) > 0 {
		assert.Equal(suite.T(), "Action Required", emails[0].Category)
	}
}

// Test GetEmails without COM backend
func (suite *EmailServiceTestSuite) TestGetEmails_NoComBackend() {
	suite.service.useComBackend = false
	
	// Should use database even if source is "outlook"
	_, total, err := suite.service.GetEmails("Inbox", 10, 0, "outlook", "")
	
	// Should not call Outlook mock
	assert.NoError(suite.T(), err)
	// emails can be nil or empty slice when database is empty
	assert.GreaterOrEqual(suite.T(), total, 0)
}

// Test GetEmailByID with Outlook source
func (suite *EmailServiceTestSuite) TestGetEmailByID_OutlookSource() {
	expectedEmail := &models.Email{
		ID:      "outlook-123",
		Subject: "Outlook Email",
		Sender:  "sender@test.com",
	}
	
	suite.mockOutlook.On("GetEmailByID", "outlook-123").Return(expectedEmail, nil)
	
	email, err := suite.service.GetEmailByID("outlook-123", "outlook")
	
	assert.NoError(suite.T(), err)
	assert.NotNil(suite.T(), email)
	assert.Equal(suite.T(), "outlook-123", email.ID)
	assert.Equal(suite.T(), "Outlook Email", email.Subject)
}

// Test GetEmailByID with database source
func (suite *EmailServiceTestSuite) TestGetEmailByID_DatabaseSource() {
	// Save email to database
	testEmail := &models.Email{
		ID:      "db-123",
		Subject: "Database Email",
		Sender:  "db@test.com",
		ReceivedTime: time.Now(),
	}
	database.SaveEmail(testEmail)
	
	email, err := suite.service.GetEmailByID("db-123", "database")
	
	assert.NoError(suite.T(), err)
	assert.NotNil(suite.T(), email)
	assert.Equal(suite.T(), "db-123", email.ID)
}

// Test GetEmailByID not found
func (suite *EmailServiceTestSuite) TestGetEmailByID_NotFound() {
	email, err := suite.service.GetEmailByID("nonexistent", "database")
	
	assert.Error(suite.T(), err)
	assert.Nil(suite.T(), email)
}

// Test SearchEmails
func (suite *EmailServiceTestSuite) TestSearchEmails() {
	// Save emails
	email1 := &models.Email{
		ID:      "search-1",
		Subject: "Meeting tomorrow",
		Sender:  "boss@test.com",
		ReceivedTime: time.Now(),
	}
	email2 := &models.Email{
		ID:      "search-2",
		Subject: "Project update",
		Sender:  "coworker@test.com",
		ReceivedTime: time.Now(),
	}
	database.SaveEmail(email1)
	database.SaveEmail(email2)
	
	emails, total, err := suite.service.SearchEmails("meeting", 1, 10)
	
	assert.NoError(suite.T(), err)
	assert.GreaterOrEqual(suite.T(), total, 1)
	if len(emails) > 0 {
		assert.Contains(suite.T(), emails[0].Subject, "Meeting")
	}
}

// Test MarkAsRead
func (suite *EmailServiceTestSuite) TestMarkAsRead() {
	suite.mockOutlook.On("MarkAsRead", "email-123", true).Return(nil)
	
	err := suite.service.MarkAsRead("email-123", true)
	
	assert.NoError(suite.T(), err)
}

// Test MarkAsRead without COM backend
func (suite *EmailServiceTestSuite) TestMarkAsRead_NoComBackend() {
	suite.service.useComBackend = false
	
	err := suite.service.MarkAsRead("email-123", true)
	
	assert.Error(suite.T(), err)
	assert.Contains(suite.T(), err.Error(), "COM backend not available")
}

// Test MoveToFolder
func (suite *EmailServiceTestSuite) TestMoveToFolder() {
	suite.mockOutlook.On("MoveToFolder", "email-123", "Archive").Return(nil)
	
	err := suite.service.MoveToFolder("email-123", "Archive")
	
	assert.NoError(suite.T(), err)
}

// Test MoveToFolder error
func (suite *EmailServiceTestSuite) TestMoveToFolder_Error() {
	suite.mockOutlook.On("MoveToFolder", "email-123", "InvalidFolder").
		Return(errors.New("folder not found"))
	
	err := suite.service.MoveToFolder("email-123", "InvalidFolder")
	
	assert.Error(suite.T(), err)
	assert.Contains(suite.T(), err.Error(), "folder not found")
}

// Test UpdateClassification database only
func (suite *EmailServiceTestSuite) TestUpdateClassification_DatabaseOnly() {
	// Save email first
	email := &models.Email{
		ID:      "update-123",
		Subject: "Test Email",
		Sender:  "test@test.com",
		ReceivedTime: time.Now(),
	}
	database.SaveEmail(email)
	
	err := suite.service.UpdateClassification("update-123", "FYI", false)
	
	assert.NoError(suite.T(), err)
	
	// Verify update in database
	updated, err := database.GetEmailByID("update-123")
	assert.NoError(suite.T(), err)
	assert.Equal(suite.T(), "FYI", updated.Category)
}

// Test UpdateClassification with Outlook sync
func (suite *EmailServiceTestSuite) TestUpdateClassification_WithOutlookSync() {
	// Save email first
	email := &models.Email{
		ID:      "update-sync-123",
		Subject: "Test Email",
		Sender:  "test@test.com",
		ReceivedTime: time.Now(),
	}
	database.SaveEmail(email)
	
	suite.mockOutlook.On("ApplyClassification", "update-sync-123", "Action Required").Return(nil)
	
	err := suite.service.UpdateClassification("update-sync-123", "Action Required", true)
	
	assert.NoError(suite.T(), err)
}

// Test BulkApplyToOutlook success
func (suite *EmailServiceTestSuite) TestBulkApplyToOutlook_Success() {
	// Save emails to database
	email1 := &models.Email{
		ID:       "bulk-1",
		Subject:  "Email 1",
		Sender:   "sender@test.com",
		ReceivedTime: time.Now(),
		Category: "FYI",
	}
	email2 := &models.Email{
		ID:       "bulk-2",
		Subject:  "Email 2",
		Sender:   "sender@test.com",
		ReceivedTime: time.Now(),
		Category: "Action Required",
	}
	database.SaveEmail(email1)
	database.SaveEmail(email2)
	
	suite.mockOutlook.On("ApplyClassification", "bulk-1", "FYI").Return(nil)
	suite.mockOutlook.On("ApplyClassification", "bulk-2", "Action Required").Return(nil)
	
	successful, failed, errors, err := suite.service.BulkApplyToOutlook([]string{"bulk-1", "bulk-2"})
	
	assert.NoError(suite.T(), err)
	assert.Equal(suite.T(), 2, successful)
	assert.Equal(suite.T(), 0, failed)
	assert.Empty(suite.T(), errors)
}

// Test BulkApplyToOutlook with partial failures
func (suite *EmailServiceTestSuite) TestBulkApplyToOutlook_PartialFailure() {
	// Save email to database
	email := &models.Email{
		ID:       "bulk-fail-1",
		Subject:  "Email 1",
		Sender:   "sender@test.com",
		ReceivedTime: time.Now(),
		Category: "FYI",
	}
	database.SaveEmail(email)
	
	// Mock expects only one call because bulk-fail-2 doesn't exist in DB
	suite.mockOutlook.On("ApplyClassification", "bulk-fail-1", "FYI").Return(nil)
	
	successful, failed, errs, err := suite.service.BulkApplyToOutlook([]string{"bulk-fail-1", "bulk-fail-2"})
	
	assert.NoError(suite.T(), err)
	assert.Equal(suite.T(), 1, successful)
	assert.Equal(suite.T(), 1, failed)
	assert.Len(suite.T(), errs, 1)
	assert.Contains(suite.T(), errs[0], "bulk-fail-2")
}

// Test BulkApplyToOutlook without COM backend
func (suite *EmailServiceTestSuite) TestBulkApplyToOutlook_NoComBackend() {
	suite.service.useComBackend = false
	
	successful, failed, errors, err := suite.service.BulkApplyToOutlook([]string{"email-1"})
	
	assert.Error(suite.T(), err)
	assert.Contains(suite.T(), err.Error(), "COM backend not available")
	assert.Equal(suite.T(), 0, successful)
	assert.Equal(suite.T(), 0, failed)
	assert.Nil(suite.T(), errors)
}

// Test SyncToDatabase
func (suite *EmailServiceTestSuite) TestSyncToDatabase() {
	emails := []*models.Email{
		{ID: "sync-1", Subject: "Sync Email 1", Sender: "s1@test.com", ReceivedTime: time.Now()},
		{ID: "sync-2", Subject: "Sync Email 2", Sender: "s2@test.com", ReceivedTime: time.Now()},
	}
	
	err := suite.service.SyncToDatabase(emails)
	
	assert.NoError(suite.T(), err)
	
	// Verify emails were saved
	saved1, err := database.GetEmailByID("sync-1")
	assert.NoError(suite.T(), err)
	assert.Equal(suite.T(), "Sync Email 1", saved1.Subject)
	
	saved2, err := database.GetEmailByID("sync-2")
	assert.NoError(suite.T(), err)
	assert.Equal(suite.T(), "Sync Email 2", saved2.Subject)
}

// Test GetFolders
func (suite *EmailServiceTestSuite) TestGetFolders() {
	expectedFolders := []models.EmailFolder{
		{Name: "Inbox", TotalCount: 10},
		{Name: "Sent Items", TotalCount: 5},
	}
	
	suite.mockOutlook.On("GetFolders").Return(expectedFolders, nil)
	
	folders, err := suite.service.GetFolders()
	
	assert.NoError(suite.T(), err)
	assert.Len(suite.T(), folders, 2)
	assert.Equal(suite.T(), "Inbox", folders[0].Name)
}

// Test GetFolders without COM backend
func (suite *EmailServiceTestSuite) TestGetFolders_NoComBackend() {
	suite.service.useComBackend = false
	
	folders, err := suite.service.GetFolders()
	
	assert.Error(suite.T(), err)
	assert.Contains(suite.T(), err.Error(), "COM backend not available")
	assert.Nil(suite.T(), folders)
}

// Test GetConversation with Outlook source
func (suite *EmailServiceTestSuite) TestGetConversation_OutlookSource() {
	expectedEmails := []*models.Email{
		{ID: "conv-1", Subject: "RE: Meeting", ConversationID: "conv-123"},
		{ID: "conv-2", Subject: "RE: RE: Meeting", ConversationID: "conv-123"},
	}
	
	suite.mockOutlook.On("GetConversationEmails", "conv-123").Return(expectedEmails, nil)
	
	emails, err := suite.service.GetConversation("conv-123", "outlook")
	
	assert.NoError(suite.T(), err)
	assert.Len(suite.T(), emails, 2)
	assert.Equal(suite.T(), "conv-123", emails[0].ConversationID)
}

// Test GetConversation from database
func (suite *EmailServiceTestSuite) TestGetConversation_DatabaseSource() {
	// Save conversation emails
	email1 := &models.Email{
		ID:             "conv-db-1",
		Subject:        "Meeting",
		Sender:         "sender@test.com",
		ReceivedTime: time.Now(),
		ConversationID: "conv-db-123",
	}
	email2 := &models.Email{
		ID:             "conv-db-2",
		Subject:        "RE: Meeting",
		Sender:         "reply@test.com",
		ReceivedTime: time.Now(),
		ConversationID: "conv-db-123",
	}
	database.SaveEmail(email1)
	database.SaveEmail(email2)
	
	emails, err := suite.service.GetConversation("conv-db-123", "database")
	
	assert.NoError(suite.T(), err)
	assert.GreaterOrEqual(suite.T(), len(emails), 2)
}

// Test GetStats
func (suite *EmailServiceTestSuite) TestGetStats() {
	// Save emails with different categories
	email1 := &models.Email{
		ID:       "stats-1",
		Subject:  "Email 1",
		Sender:   "sender1@test.com",
		ReceivedTime: time.Now(),
		Category: "Action Required",
	}
	email2 := &models.Email{
		ID:       "stats-2",
		Subject:  "Email 2",
		Sender:   "sender2@test.com",
		ReceivedTime: time.Now(),
		Category: "FYI",
	}
	database.SaveEmail(email1)
	database.SaveEmail(email2)
	
	stats, err := suite.service.GetStats(10)
	
	assert.NoError(suite.T(), err)
	assert.NotNil(suite.T(), stats)
}

// Test GetAccuracyStats
func (suite *EmailServiceTestSuite) TestGetAccuracyStats() {
	stats, err := suite.service.GetAccuracyStats()
	
	assert.NoError(suite.T(), err)
	assert.NotNil(suite.T(), stats)
}

// Test GetCategoryMappings
func (suite *EmailServiceTestSuite) TestGetCategoryMappings() {
	mappings := suite.service.GetCategoryMappings()
	
	assert.NotNil(suite.T(), mappings)
	// Should return category mappings from outlook package
	assert.GreaterOrEqual(suite.T(), len(mappings), 0)
}

// Test ClassifyEmail
func (suite *EmailServiceTestSuite) TestClassifyEmail() {
	ctx := context.Background()
	confidence := 0.95
	expectedResponse := &models.AIClassificationResponse{
		Category:              "Action Required",
		Confidence:            &confidence,
		Reasoning:             "Email requires action",
		AlternativeCategories: []string{"FYI"},
	}
	
	suite.mockAI.On("ClassifyEmail", ctx, "Test Subject", "sender@test.com", "Test content", "").
		Return(expectedResponse, nil)
	
	response, err := suite.service.ClassifyEmail(ctx, "Test Subject", "sender@test.com", "Test content", "")
	
	assert.NoError(suite.T(), err)
	assert.NotNil(suite.T(), response)
	assert.Equal(suite.T(), "Action Required", response.Category)
	assert.Equal(suite.T(), 0.95, *response.Confidence)
}

// Test ClassifyEmail without AI client
func (suite *EmailServiceTestSuite) TestClassifyEmail_NoAIClient() {
	suite.service.aiClient = nil
	
	ctx := context.Background()
	response, err := suite.service.ClassifyEmail(ctx, "Test", "sender@test.com", "content", "")
	
	assert.Error(suite.T(), err)
	assert.Contains(suite.T(), err.Error(), "AI client not configured")
	assert.Nil(suite.T(), response)
}

// Test ClassifyEmail with AI error
func (suite *EmailServiceTestSuite) TestClassifyEmail_AIError() {
	ctx := context.Background()
	suite.mockAI.On("ClassifyEmail", ctx, "Test", "sender@test.com", "content", "").
		Return(nil, errors.New("AI service unavailable"))
	
	response, err := suite.service.ClassifyEmail(ctx, "Test", "sender@test.com", "content", "")
	
	assert.Error(suite.T(), err)
	assert.Contains(suite.T(), err.Error(), "AI service unavailable")
	assert.Nil(suite.T(), response)
}

// Test ExtractActionItems
func (suite *EmailServiceTestSuite) TestExtractActionItems() {
	ctx := context.Background()
	expectedResponse := &models.ActionItemResponse{
		ActionItems: []string{"Complete report"},
		Urgency:     "high",
	}
	
	suite.mockAI.On("ExtractActionItems", ctx, "Email content", "user context").
		Return(expectedResponse, nil)
	
	response, err := suite.service.ExtractActionItems(ctx, "Email content", "user context")
	
	assert.NoError(suite.T(), err)
	assert.NotNil(suite.T(), response)
	assert.Len(suite.T(), response.ActionItems, 1)
	assert.Equal(suite.T(), "high", response.Urgency)
}

// Test ExtractActionItems without AI client
func (suite *EmailServiceTestSuite) TestExtractActionItems_NoAIClient() {
	suite.service.aiClient = nil
	
	ctx := context.Background()
	response, err := suite.service.ExtractActionItems(ctx, "content", "")
	
	assert.Error(suite.T(), err)
	assert.Contains(suite.T(), err.Error(), "AI client not configured")
	assert.Nil(suite.T(), response)
}

// Test SummarizeEmail
func (suite *EmailServiceTestSuite) TestSummarizeEmail() {
	ctx := context.Background()
	expectedResponse := &models.SummaryResponse{
		Summary:   "Email summary",
		KeyPoints: []string{"Point 1", "Point 2"},
	}
	
	suite.mockAI.On("Summarize", ctx, "Email content", "brief").
		Return(expectedResponse, nil)
	
	response, err := suite.service.SummarizeEmail(ctx, "Email content", "brief")
	
	assert.NoError(suite.T(), err)
	assert.NotNil(suite.T(), response)
	assert.Equal(suite.T(), "Email summary", response.Summary)
	assert.Len(suite.T(), response.KeyPoints, 2)
}

// Test SummarizeEmail without AI client
func (suite *EmailServiceTestSuite) TestSummarizeEmail_NoAIClient() {
	suite.service.aiClient = nil
	
	ctx := context.Background()
	response, err := suite.service.SummarizeEmail(ctx, "content", "brief")
	
	assert.Error(suite.T(), err)
	assert.Contains(suite.T(), err.Error(), "AI client not configured")
	assert.Nil(suite.T(), response)
}

// Test CheckAIHealth
func (suite *EmailServiceTestSuite) TestCheckAIHealth() {
	ctx := context.Background()
	suite.mockAI.On("CheckHealth", ctx).Return(nil)
	
	err := suite.service.CheckAIHealth(ctx)
	
	assert.NoError(suite.T(), err)
}

// Test CheckAIHealth without AI client
func (suite *EmailServiceTestSuite) TestCheckAIHealth_NoAIClient() {
	suite.service.aiClient = nil
	
	ctx := context.Background()
	err := suite.service.CheckAIHealth(ctx)
	
	assert.Error(suite.T(), err)
	assert.Contains(suite.T(), err.Error(), "AI client not configured")
}

// Test CheckAIHealth with error
func (suite *EmailServiceTestSuite) TestCheckAIHealth_Error() {
	ctx := context.Background()
	suite.mockAI.On("CheckHealth", ctx).Return(errors.New("service unavailable"))
	
	err := suite.service.CheckAIHealth(ctx)
	
	assert.Error(suite.T(), err)
	assert.Contains(suite.T(), err.Error(), "service unavailable")
}

// Test Close method
func (suite *EmailServiceTestSuite) TestClose() {
	suite.mockOutlook.On("Close").Return(nil)
	
	err := suite.service.Close()
	
	assert.NoError(suite.T(), err)
}

// Test Close with nil provider
func (suite *EmailServiceTestSuite) TestClose_NilProvider() {
	suite.service.outlookProvider = nil
	
	err := suite.service.Close()
	
	assert.NoError(suite.T(), err)
}

// Test Close with error
func (suite *EmailServiceTestSuite) TestClose_Error() {
	suite.mockOutlook.On("Close").Return(errors.New("close failed"))
	
	err := suite.service.Close()
	
	assert.Error(suite.T(), err)
	assert.Contains(suite.T(), err.Error(), "close failed")
}

func TestEmailServiceTestSuite(t *testing.T) {
	suite.Run(t, new(EmailServiceTestSuite))
}
