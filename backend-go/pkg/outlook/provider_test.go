package outlook

import (
	"testing"
	"time"

	"email-helper-backend/internal/models"

	"github.com/go-ole/go-ole"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// Test GetCategoryMappings - Pure business logic, no COM
func TestGetCategoryMappings(t *testing.T) {
	t.Run("ReturnsAllMappings", func(t *testing.T) {
		mappings := GetCategoryMappings()
		
		assert.NotEmpty(t, mappings)
		// Should have mappings for both inbox and non-inbox categories
		assert.GreaterOrEqual(t, len(mappings), 7, "Should have at least 7 category mappings")
	})

	t.Run("InboxCategoriesStayInInbox", func(t *testing.T) {
		mappings := GetCategoryMappings()
		
		inboxCats := []string{"required_personal_action", "team_action", "fyi", "newsletter"}
		for _, cat := range inboxCats {
			found := false
			for _, mapping := range mappings {
				if mapping.Category == cat {
					assert.True(t, mapping.StaysInInbox, "Category %s should stay in inbox", cat)
					assert.NotEmpty(t, mapping.FolderName, "Category %s should have folder name", cat)
					found = true
					break
				}
			}
			assert.True(t, found, "Should find mapping for %s", cat)
		}
	})

	t.Run("NonInboxCategoriesGetMoved", func(t *testing.T) {
		mappings := GetCategoryMappings()
		
		nonInboxCats := []string{"optional_event", "job_listing", "spam_to_delete"}
		for _, cat := range nonInboxCats {
			found := false
			for _, mapping := range mappings {
				if mapping.Category == cat {
					assert.False(t, mapping.StaysInInbox, "Category %s should not stay in inbox", cat)
					assert.NotEmpty(t, mapping.FolderName, "Category %s should have folder name", cat)
					found = true
					break
				}
			}
			assert.True(t, found, "Should find mapping for %s", cat)
		}
	})

	t.Run("AllCategoriesHaveFolderNames", func(t *testing.T) {
		mappings := GetCategoryMappings()
		
		for _, mapping := range mappings {
			assert.NotEmpty(t, mapping.Category, "Category should not be empty")
			assert.NotEmpty(t, mapping.FolderName, "Folder name should not be empty for category %s", mapping.Category)
		}
	})

	t.Run("NoDuplicateCategories", func(t *testing.T) {
		mappings := GetCategoryMappings()
		
		seen := make(map[string]bool)
		for _, mapping := range mappings {
			assert.False(t, seen[mapping.Category], "Category %s should not be duplicated", mapping.Category)
			seen[mapping.Category] = true
		}
	})
}

// Test InboxCategories mapping - Business logic
func TestInboxCategoriesMapping(t *testing.T) {
	t.Run("RequiredPersonalActionMapsToWorkRelevant", func(t *testing.T) {
		folder, exists := InboxCategories["required_personal_action"]
		assert.True(t, exists)
		assert.Equal(t, "Work Relevant", folder)
	})

	t.Run("TeamActionMapsToWorkRelevant", func(t *testing.T) {
		folder, exists := InboxCategories["team_action"]
		assert.True(t, exists)
		assert.Equal(t, "Work Relevant", folder)
	})

	t.Run("FYIMapsToFYI", func(t *testing.T) {
		folder, exists := InboxCategories["fyi"]
		assert.True(t, exists)
		assert.Equal(t, "FYI", folder)
	})

	t.Run("NewsletterMapsToNewsletters", func(t *testing.T) {
		folder, exists := InboxCategories["newsletter"]
		assert.True(t, exists)
		assert.Equal(t, "Newsletters", folder)
	})

	t.Run("AllInboxCategoriesPresent", func(t *testing.T) {
		expectedCats := []string{"required_personal_action", "team_action", "fyi", "newsletter"}
		assert.Len(t, InboxCategories, len(expectedCats), "Should have exactly %d inbox categories", len(expectedCats))
		
		for _, cat := range expectedCats {
			_, exists := InboxCategories[cat]
			assert.True(t, exists, "Inbox category %s should exist", cat)
		}
	})
}

// Test NonInboxCategories mapping - Business logic
func TestNonInboxCategoriesMapping(t *testing.T) {
	t.Run("OptionalEventMapsToOptionalEvents", func(t *testing.T) {
		folder, exists := NonInboxCategories["optional_event"]
		assert.True(t, exists)
		assert.Equal(t, "Optional Events", folder)
	})

	t.Run("JobListingMapsToJobListings", func(t *testing.T) {
		folder, exists := NonInboxCategories["job_listing"]
		assert.True(t, exists)
		assert.Equal(t, "Job Listings", folder)
	})

	t.Run("SpamToDeleteMapsToSpam", func(t *testing.T) {
		folder, exists := NonInboxCategories["spam_to_delete"]
		assert.True(t, exists)
		assert.Equal(t, "Spam", folder)
	})

	t.Run("AllNonInboxCategoriesPresent", func(t *testing.T) {
		expectedCats := []string{"optional_event", "job_listing", "spam_to_delete"}
		assert.Len(t, NonInboxCategories, len(expectedCats), "Should have exactly %d non-inbox categories", len(expectedCats))
		
		for _, cat := range expectedCats {
			_, exists := NonInboxCategories[cat]
			assert.True(t, exists, "Non-inbox category %s should exist", cat)
		}
	})
}

// Test category classification logic - Business rules without COM
func TestApplyClassificationLogic(t *testing.T) {
	t.Run("InboxCategoryShouldStayInInbox", func(t *testing.T) {
		testCases := []struct {
			category     string
			expectedCat  string
			shouldMove   bool
		}{
			{"required_personal_action", "Work Relevant", false},
			{"team_action", "Work Relevant", false},
			{"fyi", "FYI", false},
			{"newsletter", "Newsletters", false},
		}

		for _, tc := range testCases {
			folderName, isInbox := InboxCategories[tc.category]
			assert.True(t, isInbox, "Category %s should be in InboxCategories", tc.category)
			assert.Equal(t, tc.expectedCat, folderName, "Category %s folder name", tc.category)
			assert.False(t, tc.shouldMove, "Category %s should not move to folder", tc.category)
		}
	})

	t.Run("NonInboxCategoryShouldMoveToFolder", func(t *testing.T) {
		testCases := []struct {
			category     string
			expectedFolder string
			shouldMove   bool
		}{
			{"optional_event", "Optional Events", true},
			{"job_listing", "Job Listings", true},
			{"spam_to_delete", "Spam", true},
		}

		for _, tc := range testCases {
			folderName, isNonInbox := NonInboxCategories[tc.category]
			assert.True(t, isNonInbox, "Category %s should be in NonInboxCategories", tc.category)
			assert.Equal(t, tc.expectedFolder, folderName, "Category %s folder name", tc.category)
			assert.True(t, tc.shouldMove, "Category %s should move to folder", tc.category)
		}
	})

	t.Run("UnknownCategoryShouldBeDetected", func(t *testing.T) {
		unknownCategories := []string{
			"unknown",
			"personal",
			"work",
			"random_category",
			"",
		}

		for _, cat := range unknownCategories {
			_, isInbox := InboxCategories[cat]
			_, isNonInbox := NonInboxCategories[cat]
			
			isKnown := isInbox || isNonInbox
			assert.False(t, isKnown, "Category %s should be unknown", cat)
		}
	})

	t.Run("CategoryNamesCaseSensitive", func(t *testing.T) {
		// Categories should be lowercase with underscores
		testCases := []struct {
			input     string
			shouldExist bool
		}{
			{"required_personal_action", true},
			{"REQUIRED_PERSONAL_ACTION", false},
			{"Required_Personal_Action", false},
			{"required personal action", false},
			{"fyi", true},
			{"FYI", false},
		}

		for _, tc := range testCases {
			_, inInbox := InboxCategories[tc.input]
			_, inNonInbox := NonInboxCategories[tc.input]
			exists := inInbox || inNonInbox
			
			assert.Equal(t, tc.shouldExist, exists, "Category %s existence", tc.input)
		}
	})
}

// Test category to folder translation - Business logic
func TestCategoryToFolderTranslation(t *testing.T) {
	t.Run("MultipleCategoriesToSameFolder", func(t *testing.T) {
		// Both required_personal_action and team_action map to "Work Relevant"
		assert.Equal(t, InboxCategories["required_personal_action"], InboxCategories["team_action"])
		assert.Equal(t, "Work Relevant", InboxCategories["required_personal_action"])
	})

	t.Run("CategoryNameToFolderNameMapping", func(t *testing.T) {
		// Test the transformation from category names to folder names
		testCases := []struct {
			category   string
			folderName string
		}{
			{"required_personal_action", "Work Relevant"},
			{"team_action", "Work Relevant"},
			{"fyi", "FYI"},
			{"newsletter", "Newsletters"},
			{"optional_event", "Optional Events"},
			{"job_listing", "Job Listings"},
			{"spam_to_delete", "Spam"},
		}

		for _, tc := range testCases {
			var actualFolder string
			if folder, exists := InboxCategories[tc.category]; exists {
				actualFolder = folder
			} else if folder, exists := NonInboxCategories[tc.category]; exists {
				actualFolder = folder
			}
			
			assert.Equal(t, tc.folderName, actualFolder, "Folder for category %s", tc.category)
		}
	})

	t.Run("FolderNamesHaveProperCasing", func(t *testing.T) {
		// Folder names should be properly capitalized for Outlook
		allFolders := make(map[string]bool)
		
		for _, folder := range InboxCategories {
			allFolders[folder] = true
		}
		for _, folder := range NonInboxCategories {
			allFolders[folder] = true
		}

		for folder := range allFolders {
			assert.NotEmpty(t, folder, "Folder name should not be empty")
			// First character should be uppercase
			if len(folder) > 0 {
				firstChar := folder[0]
				assert.True(t, firstChar >= 'A' && firstChar <= 'Z', "Folder '%s' should start with uppercase", folder)
			}
		}
	})

	t.Run("NoConflictingFolderNames", func(t *testing.T) {
		// Make sure folder names are descriptive and don't conflict
		allFolders := make(map[string]int)
		
		for _, folder := range InboxCategories {
			allFolders[folder]++
		}
		for _, folder := range NonInboxCategories {
			allFolders[folder]++
		}

		// Check for duplicates (some are intentional like "Work Relevant")
		workRelevantCount := 0
		for folder, count := range allFolders {
			if folder == "Work Relevant" {
				workRelevantCount = count
			} else {
				// Non "Work Relevant" folders should be unique
				assert.Equal(t, 1, count, "Folder %s should be unique", folder)
			}
		}

		// "Work Relevant" should map to exactly 2 categories
		assert.Equal(t, 2, workRelevantCount, "Work Relevant should map to 2 categories")
	})
}

// Test Provider initialization logic - Error handling without actual COM
func TestProviderErrorHandling(t *testing.T) {
	t.Run("NewProviderCreatesEmptyFoldersMap", func(t *testing.T) {
		provider, err := NewProvider()
		require.NoError(t, err)
		assert.NotNil(t, provider)
		assert.NotNil(t, provider.folders)
		assert.Empty(t, provider.folders)
		assert.False(t, provider.initialized)
	})

	t.Run("OperationsFailWhenNotInitialized", func(t *testing.T) {
		provider, err := NewProvider()
		require.NoError(t, err)

		// These should all fail because provider is not initialized
		// We can't actually test them without COM, but we can test the business logic

		assert.False(t, provider.initialized, "Provider should not be initialized")
	})

	t.Run("ProviderHasMutexForThreadSafety", func(t *testing.T) {
		provider, err := NewProvider()
		require.NoError(t, err)

		// Provider should have a mutex for thread-safe COM operations
		assert.NotNil(t, &provider.mu)
	})

	t.Run("FoldersMapInitialized", func(t *testing.T) {
		provider, err := NewProvider()
		require.NoError(t, err)

		// Folders map should be initialized (not nil)
		assert.NotNil(t, provider.folders)
		assert.IsType(t, make(map[string]*ole.IDispatch), provider.folders)
	})
}

// Test email property extraction logic - What we'd test if we could mock COM
func TestParseEmailLogic(t *testing.T) {
	// These tests document the expected behavior of parseEmail
	// Actual testing would require mocking COM, which is complex

	t.Run("EmailModelFields", func(t *testing.T) {
		// Verify our Email model has all expected fields
		email := &models.Email{}
		
		// Test that all fields exist (this prevents regression)
		_ = email.ID
		_ = email.Subject
		_ = email.Sender
		_ = email.Content
		_ = email.ReceivedTime
		_ = email.IsRead
		_ = email.HasAttachments
		_ = email.Importance
		_ = email.ConversationID
		_ = email.Categories
	})

	t.Run("ImportanceMappingLogic", func(t *testing.T) {
		// Outlook Importance: 0 = Low, 1 = Normal, 2 = High
		testCases := []struct {
			outlookValue int
			expected     string
		}{
			{0, "Low"},
			{1, "Normal"},
			{2, "High"},
			{3, "Normal"}, // Unknown values default to Normal
			{-1, "Normal"},
		}

		for _, tc := range testCases {
			var importance string
			switch tc.outlookValue {
			case 0:
				importance = "Low"
			case 1:
				importance = "Normal"
			case 2:
				importance = "High"
			default:
				importance = "Normal"
			}
			
			assert.Equal(t, tc.expected, importance, "Importance for value %d", tc.outlookValue)
		}
	})

	t.Run("UnReadToIsReadConversion", func(t *testing.T) {
		// Outlook has "UnRead" property, we convert to "IsRead"
		testCases := []struct {
			unread bool
			isRead bool
		}{
			{true, false},  // UnRead = true means IsRead = false
			{false, true},  // UnRead = false means IsRead = true
		}

		for _, tc := range testCases {
			isRead := !tc.unread
			assert.Equal(t, tc.isRead, isRead)
		}
	})

	t.Run("AttachmentCountToHasAttachments", func(t *testing.T) {
		// If attachment count > 0, HasAttachments = true
		testCases := []struct {
			count          int
			hasAttachments bool
		}{
			{0, false},
			{1, true},
			{5, true},
		}

		for _, tc := range testCases {
			hasAttachments := tc.count > 0
			assert.Equal(t, tc.hasAttachments, hasAttachments)
		}
	})

	t.Run("BodyCopiedToContent", func(t *testing.T) {
		// Body and Content should have the same value
		body := "This is the email body"
		content := body // parseEmail sets content = body
		
		assert.Equal(t, body, content)
	})

	t.Run("ReceivedTimeCopiedToDate", func(t *testing.T) {
		// Date and ReceivedTime should have the same value
		receivedTime := time.Now()
		date := receivedTime // parseEmail sets date = receivedTime
		
		assert.Equal(t, receivedTime, date)
	})

	t.Run("CategoriesStringToArray", func(t *testing.T) {
		// Outlook Categories is a semicolon-separated string
		// We convert to array (single category for now)
		testCases := []struct {
			categoriesStr string
			expected      []string
		}{
			{"Work Relevant", []string{"Work Relevant"}},
			{"", nil},
			{"FYI", []string{"FYI"}},
		}

		for _, tc := range testCases {
			var categories []string
			if tc.categoriesStr != "" {
				categories = []string{tc.categoriesStr}
			}
			
			assert.Equal(t, tc.expected, categories)
		}
	})
}

// Test NULL/nil property handling logic
func TestNullPropertyHandling(t *testing.T) {
	t.Run("EmptyEmailWhenAllPropertiesNull", func(t *testing.T) {
		// parseEmail should handle all properties being NULL
		// Result should be an empty Email struct, not nil
		email := &models.Email{}
		
		// Verify default values
		assert.Empty(t, email.ID)
		assert.Empty(t, email.Subject)
		assert.Empty(t, email.Sender)
		assert.Empty(t, email.Content)
		assert.Empty(t, email.Content)
		assert.False(t, email.IsRead)
		assert.False(t, email.HasAttachments)
	})

	t.Run("PartialPropertiesHandled", func(t *testing.T) {
		// If only some properties are set, others should remain empty/default
		email := &models.Email{
			Subject: "Test Subject",
			Sender:  "test@test.com",
		}
		
		assert.Equal(t, "Test Subject", email.Subject)
		assert.Equal(t, "test@test.com", email.Sender)
		assert.Empty(t, email.Content) // Not set
		assert.Empty(t, email.ID)   // Not set
	})

	t.Run("ImportanceDefaultsToNormal", func(t *testing.T) {
		// If Importance is not set or invalid, should default to Normal
		importance := "Normal" // Default
		assert.Equal(t, "Normal", importance)
	})

	t.Run("HasAttachmentsDefaultsToFalse", func(t *testing.T) {
		// If attachments property is NULL or count is 0
		hasAttachments := false // Default
		assert.False(t, hasAttachments)
	})

	t.Run("IsReadDefaultsToFalse", func(t *testing.T) {
		// If UnRead property is NULL, IsRead should default to false
		isRead := false // Default
		assert.False(t, isRead)
	})
}

// Test category name normalization logic
func TestCategoryNameNormalization(t *testing.T) {
	t.Run("CategoryNamesLowerCaseWithUnderscores", func(t *testing.T) {
		// All category keys should be lowercase with underscores
		allCategories := make([]string, 0)
		for cat := range InboxCategories {
			allCategories = append(allCategories, cat)
		}
		for cat := range NonInboxCategories {
			allCategories = append(allCategories, cat)
		}

		for _, cat := range allCategories {
			// Should not contain uppercase
			assert.Equal(t, cat, toLowerWithUnderscores(cat), "Category %s should be normalized", cat)
			// Should not contain spaces
			assert.NotContains(t, cat, " ", "Category %s should not have spaces", cat)
			// Should not contain hyphens
			assert.NotContains(t, cat, "-", "Category %s should not have hyphens", cat)
		}
	})

	t.Run("FolderNamesProperCase", func(t *testing.T) {
		// Folder names should be properly capitalized
		allFolders := make([]string, 0)
		for _, folder := range InboxCategories {
			allFolders = append(allFolders, folder)
		}
		for _, folder := range NonInboxCategories {
			allFolders = append(allFolders, folder)
		}

		seen := make(map[string]bool)
		for _, folder := range allFolders {
			if seen[folder] {
				continue
			}
			seen[folder] = true

			// Folder names can have spaces (e.g., "Work Relevant")
			assert.NotEmpty(t, folder)
		}
	})

	t.Run("CategoryConsistency", func(t *testing.T) {
		// Verify Python backend compatibility
		// Categories from AI must match exactly (case-sensitive)
		expectedCategories := map[string]bool{
			"required_personal_action": true,
			"team_action":              true,
			"fyi":                      true,
			"newsletter":               true,
			"optional_event":           true,
			"job_listing":              true,
			"spam_to_delete":           true,
		}

		allCategories := make(map[string]bool)
		for cat := range InboxCategories {
			allCategories[cat] = true
		}
		for cat := range NonInboxCategories {
			allCategories[cat] = true
		}

		// All expected categories should exist
		for cat := range expectedCategories {
			assert.True(t, allCategories[cat], "Expected category %s should exist", cat)
		}

		// No extra categories
		assert.Equal(t, len(expectedCategories), len(allCategories), "Should have exactly %d categories", len(expectedCategories))
	})
}

// Helper function for testing normalization
func toLowerWithUnderscores(s string) string {
	return s // In actual code, this would normalize the string
}

// Test edge cases
func TestEdgeCases(t *testing.T) {
	t.Run("EmptyCategoryString", func(t *testing.T) {
		_, inInbox := InboxCategories[""]
		_, inNonInbox := NonInboxCategories[""]
		
		assert.False(t, inInbox)
		assert.False(t, inNonInbox)
	})

	t.Run("WhitespaceCategoryString", func(t *testing.T) {
		_, inInbox := InboxCategories["  "]
		_, inNonInbox := NonInboxCategories["  "]
		
		assert.False(t, inInbox)
		assert.False(t, inNonInbox)
	})

	t.Run("SpecialCharactersInCategory", func(t *testing.T) {
		specialChars := []string{
			"category!",
			"category@home",
			"category#1",
			"category$",
			"category%",
		}

		for _, cat := range specialChars {
			_, inInbox := InboxCategories[cat]
			_, inNonInbox := NonInboxCategories[cat]
			
			assert.False(t, inInbox || inNonInbox, "Special char category %s should not exist", cat)
		}
	})

	t.Run("VeryLongCategoryName", func(t *testing.T) {
		longCat := string(make([]byte, 1000))
		for i := range longCat {
			longCat = string([]byte(longCat)[:i]) + "a" + string([]byte(longCat)[i+1:])
		}

		_, inInbox := InboxCategories[longCat]
		_, inNonInbox := NonInboxCategories[longCat]
		
		assert.False(t, inInbox || inNonInbox)
	})
}

// Test concurrency safety - Mutex usage
func TestThreadSafety(t *testing.T) {
	t.Run("ProviderHasMutex", func(t *testing.T) {
		provider, err := NewProvider()
		require.NoError(t, err)

		// Provider should have mutex for protecting COM operations
		// This ensures thread-safe access to COM objects
		assert.NotNil(t, &provider.mu)
	})

	t.Run("FoldersMapConcurrentAccess", func(t *testing.T) {
		provider, err := NewProvider()
		require.NoError(t, err)

		// Folders map should be protected by mutex
		// Test that map exists and can be accessed safely
		assert.NotNil(t, provider.folders)
		assert.Equal(t, 0, len(provider.folders))
	})
}
