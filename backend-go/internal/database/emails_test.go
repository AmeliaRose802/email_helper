package database

import (
	"sync"
	"testing"
	"time"

	"email-helper-backend/internal/models"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// setupTestDB initializes an in-memory SQLite database for testing
func setupTestDB(t *testing.T) {
	// Reset the singleton for testing
	db = nil
	once = sync.Once{}

	// Initialize with in-memory database
	err := InitDB(":memory:")
	require.NoError(t, err, "Failed to initialize test database")
}

// teardownTestDB closes the test database
func teardownTestDB(t *testing.T) {
	if db != nil {
		err := db.Close()
		assert.NoError(t, err, "Failed to close test database")
		db = nil
		once = sync.Once{}
	}
}

// createTestEmail creates a sample email for testing
func createTestEmail(id string) *models.Email {
	now := time.Now()
	confidence := 0.95
	return &models.Email{
		ID:             id,
		Subject:        "Test Subject " + id,
		Sender:         "sender@test.com",
		Recipient:      "recipient@test.com",
		Content:        "Test content for email " + id,
		ReceivedTime:   now,
		Category:       "work",
		AICategory:     "required_personal_action",
		AIConfidence:   confidence,
		AIReasoning:    "This requires immediate attention",
		OneLineSummary: "Test summary " + id,
		ConversationID: "conv-123",
	}
}

func TestSaveEmail(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	t.Run("SaveNewEmail", func(t *testing.T) {
		email := createTestEmail("email-001")
		err := SaveEmail(email)
		assert.NoError(t, err)

		// Verify email was saved
		saved, err := GetEmailByID("email-001")
		require.NoError(t, err)
		assert.Equal(t, email.ID, saved.ID)
		assert.Equal(t, email.Subject, saved.Subject)
		assert.Equal(t, email.Sender, saved.Sender)
		assert.Equal(t, email.AICategory, saved.AICategory)
		assert.Equal(t, email.AIConfidence, saved.AIConfidence)
	})

	t.Run("SaveEmailWithReplaceExisting", func(t *testing.T) {
		email := createTestEmail("email-002")
		err := SaveEmail(email)
		require.NoError(t, err)

		// Update and save again (INSERT OR REPLACE)
		email.Subject = "Updated Subject"
		email.AICategory = "fyi"
		err = SaveEmail(email)
		assert.NoError(t, err)

		// Verify update was successful
		saved, err := GetEmailByID("email-002")
		require.NoError(t, err)
		assert.Equal(t, "Updated Subject", saved.Subject)
		assert.Equal(t, "fyi", saved.AICategory)
	})

	t.Run("SaveEmailWithNullFields", func(t *testing.T) {
		email := &models.Email{
			ID:           "email-003",
			Subject:      "Minimal Email",
			Sender:       "sender@test.com",
			ReceivedTime: time.Now(),
		}
		err := SaveEmail(email)
		assert.NoError(t, err)

		saved, err := GetEmailByID("email-003")
		require.NoError(t, err)
		assert.Equal(t, "email-003", saved.ID)
		assert.Equal(t, "Minimal Email", saved.Subject)
	})
}

func TestGetEmailByID(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	t.Run("GetExistingEmail", func(t *testing.T) {
		email := createTestEmail("email-101")
		err := SaveEmail(email)
		require.NoError(t, err)

		retrieved, err := GetEmailByID("email-101")
		require.NoError(t, err)
		assert.NotNil(t, retrieved)
		assert.Equal(t, "email-101", retrieved.ID)
		assert.Equal(t, email.Subject, retrieved.Subject)
		assert.Equal(t, email.AIReasoning, retrieved.AIReasoning)
	})

	t.Run("GetNonExistentEmail", func(t *testing.T) {
		retrieved, err := GetEmailByID("nonexistent-id")
		assert.Error(t, err)
		assert.Nil(t, retrieved)
		assert.Contains(t, err.Error(), "email not found")
	})

	t.Run("GetEmailWithEmptyID", func(t *testing.T) {
		retrieved, err := GetEmailByID("")
		assert.Error(t, err)
		assert.Nil(t, retrieved)
	})
}

func TestGetEmails(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	// Create test emails with different categories
	emails := []*models.Email{
		createTestEmail("email-201"),
		createTestEmail("email-202"),
		createTestEmail("email-203"),
	}
	emails[1].AICategory = "fyi"
	emails[2].AICategory = "newsletter"

	for _, email := range emails {
		err := SaveEmail(email)
		require.NoError(t, err)
	}

	t.Run("GetAllEmailsWithPagination", func(t *testing.T) {
		retrieved, total, err := GetEmails(10, 0, "")
		require.NoError(t, err)
		assert.Equal(t, 3, total)
		assert.Len(t, retrieved, 3)
	})

	t.Run("GetEmailsWithLimitAndOffset", func(t *testing.T) {
		retrieved, total, err := GetEmails(2, 0, "")
		require.NoError(t, err)
		assert.Equal(t, 3, total)
		assert.Len(t, retrieved, 2)

		// Get second page
		retrieved, total, err = GetEmails(2, 2, "")
		require.NoError(t, err)
		assert.Equal(t, 3, total)
		assert.Len(t, retrieved, 1)
	})

	t.Run("GetEmailsByCategory", func(t *testing.T) {
		retrieved, total, err := GetEmails(10, 0, "fyi")
		require.NoError(t, err)
		assert.Equal(t, 1, total)
		assert.Len(t, retrieved, 1)
		assert.Equal(t, "fyi", retrieved[0].AICategory)
	})

	t.Run("GetEmailsWithNonExistentCategory", func(t *testing.T) {
		retrieved, total, err := GetEmails(10, 0, "nonexistent")
		require.NoError(t, err)
		assert.Equal(t, 0, total)
		assert.Len(t, retrieved, 0)
	})

	t.Run("GetEmailsOrderedByDate", func(t *testing.T) {
		// Create emails with different dates
		oldEmail := createTestEmail("email-old")
		oldEmail.ReceivedTime = time.Now().Add(-24 * time.Hour)
		err := SaveEmail(oldEmail)
		require.NoError(t, err)

		newEmail := createTestEmail("email-new")
		newEmail.ReceivedTime = time.Now()
		err = SaveEmail(newEmail)
		require.NoError(t, err)

		retrieved, _, err := GetEmails(10, 0, "")
		require.NoError(t, err)
		// First email should be newest (DESC order)
		assert.Equal(t, "email-new", retrieved[0].ID)
	})
}

func TestSearchEmails(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	// Create test emails with searchable content
	email1 := createTestEmail("search-001")
	email1.Subject = "Important meeting about project deadline"
	email1.Sender = "boss@company.com"
	err := SaveEmail(email1)
	require.NoError(t, err)

	email2 := createTestEmail("search-002")
	email2.Subject = "Weekly newsletter"
	email2.Content = "This week's highlights include important updates"
	err = SaveEmail(email2)
	require.NoError(t, err)

	email3 := createTestEmail("search-003")
	email3.Content = "Please review the quarterly report"
	err = SaveEmail(email3)
	require.NoError(t, err)

	t.Run("SearchBySubject", func(t *testing.T) {
		results, total, err := SearchEmails("meeting", 1, 10)
		require.NoError(t, err)
		assert.Equal(t, 1, total)
		assert.Len(t, results, 1)
		assert.Contains(t, results[0].Subject, "meeting")
	})

	t.Run("SearchBySender", func(t *testing.T) {
		results, total, err := SearchEmails("boss", 1, 10)
		require.NoError(t, err)
		assert.Equal(t, 1, total)
		assert.Len(t, results, 1)
		assert.Contains(t, results[0].Sender, "boss")
	})

	t.Run("SearchByContent", func(t *testing.T) {
		results, total, err := SearchEmails("highlights", 1, 10)
		require.NoError(t, err)
		assert.Equal(t, 1, total)
		assert.Len(t, results, 1)
		assert.Contains(t, results[0].Content, "highlights")
	})

	t.Run("SearchByContent", func(t *testing.T) {
		results, total, err := SearchEmails("quarterly", 1, 10)
		require.NoError(t, err)
		assert.Equal(t, 1, total)
		assert.Len(t, results, 1)
		assert.Contains(t, results[0].Content, "quarterly")
	})

	t.Run("SearchWithMultipleResults", func(t *testing.T) {
		results, total, err := SearchEmails("important", 1, 10)
		require.NoError(t, err)
		assert.Equal(t, 2, total) // Found in both email1 subject and email2 content
		assert.Len(t, results, 2)
	})

	t.Run("SearchWithPagination", func(t *testing.T) {
		// Page 1
		results, total, err := SearchEmails("Test", 1, 2)
		require.NoError(t, err)
		assert.GreaterOrEqual(t, total, 3)
		assert.Len(t, results, 2)

		// Page 2
		results, total, err = SearchEmails("Test", 2, 2)
		require.NoError(t, err)
		assert.GreaterOrEqual(t, total, 3)
		assert.GreaterOrEqual(t, len(results), 1)
	})

	t.Run("SearchNoResults", func(t *testing.T) {
		results, total, err := SearchEmails("nonexistent-term-xyz", 1, 10)
		require.NoError(t, err)
		assert.Equal(t, 0, total)
		assert.Len(t, results, 0)
	})

	t.Run("SearchWithSpecialCharacters", func(t *testing.T) {
		// SQL LIKE should handle % without treating it as wildcard
		results, total, err := SearchEmails("%meeting%", 1, 10)
		require.NoError(t, err)
		assert.Equal(t, 0, total)
		assert.Len(t, results, 0)
	})

	t.Run("SearchCaseInsensitive", func(t *testing.T) {
		_, total, err := SearchEmails("MEETING", 1, 10)
		require.NoError(t, err)
		assert.GreaterOrEqual(t, total, 1) // Should find "meeting" regardless of case
	})
}

func TestUpdateEmailClassification(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	email := createTestEmail("email-301")
	err := SaveEmail(email)
	require.NoError(t, err)

	t.Run("UpdateExistingEmail", func(t *testing.T) {
		err := UpdateEmailClassification("email-301", "fyi")
		assert.NoError(t, err)

		// Verify update
		updated, err := GetEmailByID("email-301")
		require.NoError(t, err)
		assert.Equal(t, "fyi", updated.Category)
	})

	t.Run("UpdateNonExistentEmail", func(t *testing.T) {
		err := UpdateEmailClassification("nonexistent", "fyi")
		// Should not error, just affect 0 rows
		assert.NoError(t, err)
	})

	t.Run("UpdateToEmptyCategory", func(t *testing.T) {
		err := UpdateEmailClassification("email-301", "")
		assert.NoError(t, err)

		updated, err := GetEmailByID("email-301")
		require.NoError(t, err)
		assert.Equal(t, "", updated.Category)
	})
}

func TestGetConversationEmails(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	// Create emails in same conversation with different timestamps
	now := time.Now()
	for i := 0; i < 3; i++ {
		email := createTestEmail("conv-email-" + string(rune('1'+i)))
		email.ConversationID = "conv-thread-456"
		email.ReceivedTime = now.Add(time.Duration(i) * time.Hour)
		err := SaveEmail(email)
		require.NoError(t, err)
	}

	// Create email in different conversation
	otherEmail := createTestEmail("other-email")
	otherEmail.ConversationID = "conv-thread-789"
	err := SaveEmail(otherEmail)
	require.NoError(t, err)

	t.Run("GetEmailsInConversation", func(t *testing.T) {
		results, err := GetConversationEmails("conv-thread-456")
		require.NoError(t, err)
		assert.Len(t, results, 3)
		// Verify ordering (ASC by date)
		assert.Equal(t, "conv-email-1", results[0].ID)
		assert.Equal(t, "conv-email-2", results[1].ID)
		assert.Equal(t, "conv-email-3", results[2].ID)
	})

	t.Run("GetEmailsInNonExistentConversation", func(t *testing.T) {
		results, err := GetConversationEmails("nonexistent-conv")
		require.NoError(t, err)
		assert.Len(t, results, 0)
	})

	t.Run("GetEmailsWithEmptyConversationID", func(t *testing.T) {
		results, err := GetConversationEmails("")
		require.Error(t, err)
		// Should return error for empty conversation ID
		assert.Nil(t, results)
	})
}

func TestGetEmailStats(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	// Create diverse set of emails
	categories := []string{"required_personal_action", "fyi", "newsletter", "fyi"}
	senders := []string{"alice@test.com", "bob@test.com", "alice@test.com", "charlie@test.com"}

	for i := 0; i < 4; i++ {
		email := createTestEmail("stats-email-" + string(rune('1'+i)))
		email.AICategory = categories[i]
		email.Sender = senders[i]
		err := SaveEmail(email)
		require.NoError(t, err)
	}

	t.Run("GetBasicStats", func(t *testing.T) {
		stats, err := GetEmailStats(10)
		require.NoError(t, err)
		assert.NotNil(t, stats)

		// Check total emails
		total, ok := stats["total_emails"].(int)
		assert.True(t, ok)
		assert.GreaterOrEqual(t, total, 4)
	})

	t.Run("GetEmailsByCategory", func(t *testing.T) {
		stats, err := GetEmailStats(10)
		require.NoError(t, err)

		categoryStats, ok := stats["emails_by_category"].(map[string]int)
		assert.True(t, ok)
		assert.NotNil(t, categoryStats)

		// Check expected categories
		assert.Equal(t, 1, categoryStats["required_personal_action"])
		assert.Equal(t, 2, categoryStats["fyi"])
		assert.Equal(t, 1, categoryStats["newsletter"])
	})

	t.Run("GetTopSenders", func(t *testing.T) {
		stats, err := GetEmailStats(2) // Limit to top 2
		require.NoError(t, err)

		senderStats, ok := stats["emails_by_sender"].(map[string]int)
		assert.True(t, ok)
		assert.NotNil(t, senderStats)

		// Alice should have 2 emails
		assert.Equal(t, 2, senderStats["alice@test.com"])
		// Should only have top 2 senders
		assert.LessOrEqual(t, len(senderStats), 2)
	})

	t.Run("GetEmailsWithNoEmails", func(t *testing.T) {
		// Clear database
		testDB, _ := GetDB()
		_, err := testDB.Exec("DELETE FROM emails")
		require.NoError(t, err)

		stats, err := GetEmailStats(10)
		require.NoError(t, err)
		assert.Equal(t, 0, stats["total_emails"])
	})
}

func TestGetAccuracyStats(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	t.Run("AccuracyWithCorrectClassifications", func(t *testing.T) {
		// Create emails where AI and user classifications match
		for i := 0; i < 5; i++ {
			email := createTestEmail("accuracy-correct-" + string(rune('1'+i)))
			email.AICategory = "fyi"
			email.Category = "fyi" // User agrees with AI
			email.AIConfidence = 0.9
			err := SaveEmail(email)
			require.NoError(t, err)
		}

		stats, err := GetAccuracyStats()
		require.NoError(t, err)
		assert.NotNil(t, stats)

		totalClassified, ok := stats["total_classified"].(int)
		assert.True(t, ok)
		assert.GreaterOrEqual(t, totalClassified, 5)

		userCorrected, ok := stats["user_corrected"].(int)
		assert.True(t, ok)
		assert.Equal(t, 0, userCorrected)

		accuracy, ok := stats["accuracy_percentage"].(float64)
		assert.True(t, ok)
		assert.Equal(t, 100.0, accuracy)
	})

	t.Run("AccuracyWithCorrectedClassifications", func(t *testing.T) {
		// Clear previous data
		testDB, _ := GetDB()
		_, err := testDB.Exec("DELETE FROM emails")
		require.NoError(t, err)

		// Create emails where user corrects AI
		for i := 0; i < 10; i++ {
			email := createTestEmail("accuracy-corrected-" + string(rune('1'+i)))
			email.AICategory = "fyi"
			if i < 3 {
				email.Category = "required_personal_action" // User corrects 3 out of 10
			} else {
				email.Category = "fyi"
			}
			email.AIConfidence = 0.85
			err := SaveEmail(email)
			require.NoError(t, err)
		}

		stats, err := GetAccuracyStats()
		require.NoError(t, err)

		totalClassified := stats["total_classified"].(int)
		assert.Equal(t, 10, totalClassified)

		userCorrected := stats["user_corrected"].(int)
		assert.Equal(t, 3, userCorrected)

		accuracy := stats["accuracy_percentage"].(float64)
		assert.Equal(t, 70.0, accuracy)
	})

	t.Run("AccuracyWithNullCategories", func(t *testing.T) {
		// Clear previous data
		testDB, _ := GetDB()
		_, err := testDB.Exec("DELETE FROM emails")
		require.NoError(t, err)

		// Create email without AI classification
		email := createTestEmail("no-ai-category")
		email.AICategory = ""
		email.Category = ""
		err = SaveEmail(email)
		require.NoError(t, err)

		stats, err := GetAccuracyStats()
		require.NoError(t, err)

		totalClassified := stats["total_classified"].(int)
		assert.Equal(t, 0, totalClassified) // Should not count emails without AI classification

		accuracy := stats["accuracy_percentage"].(float64)
		assert.Equal(t, 0.0, accuracy)
	})

	t.Run("AverageConfidence", func(t *testing.T) {
		// Clear previous data
		testDB, _ := GetDB()
		_, err := testDB.Exec("DELETE FROM emails")
		require.NoError(t, err)

		// Create emails with various confidence levels
		confidences := []float64{0.95, 0.85, 0.75, 0.90}
		for i, conf := range confidences {
			email := createTestEmail("conf-email-" + string(rune('1'+i)))
			email.AIConfidence = conf
			err := SaveEmail(email)
			require.NoError(t, err)
		}

		stats, err := GetAccuracyStats()
		require.NoError(t, err)

		avgConfidence, ok := stats["average_confidence"].(float64)
		assert.True(t, ok)
		expectedAvg := (0.95 + 0.85 + 0.75 + 0.90) / 4.0
		assert.InDelta(t, expectedAvg, avgConfidence, 0.01)
	})

	t.Run("AccuracyWithNoClassifiedEmails", func(t *testing.T) {
		// Clear database
		testDB, _ := GetDB()
		_, err := testDB.Exec("DELETE FROM emails")
		require.NoError(t, err)

		stats, err := GetAccuracyStats()
		require.NoError(t, err)
		assert.Equal(t, 0, stats["total_classified"])
		assert.Equal(t, 0, stats["user_corrected"])
		assert.Equal(t, 0.0, stats["accuracy_percentage"])
		assert.Equal(t, 0.0, stats["average_confidence"])
	})
}

func TestDatabaseErrors(t *testing.T) {
	t.Run("OperationsWithoutInitialization", func(t *testing.T) {
		// Reset DB to nil
		db = nil
		once = sync.Once{}

		_, err := GetEmailByID("test")
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "database not initialized")

		_, _, err = GetEmails(10, 0, "")
		assert.Error(t, err)

		err = SaveEmail(createTestEmail("test"))
		assert.Error(t, err)
	})
}
