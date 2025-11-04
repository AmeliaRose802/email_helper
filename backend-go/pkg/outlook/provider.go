package outlook

import (
	"fmt"
	"log"
	"runtime"
	"sync"
	"time"

	"email-helper-backend/internal/models"

	"github.com/go-ole/go-ole"
	"github.com/go-ole/go-ole/oleutil"
)

// Provider handles Outlook COM integration
type Provider struct {
	outlook     *ole.IDispatch
	mapi        *ole.IDispatch
	folders     map[string]*ole.IDispatch
	initialized bool
	mu          sync.Mutex // Protects COM operations
}

// NewProvider creates a new Outlook COM provider
func NewProvider() (*Provider, error) {
	return &Provider{
		folders: make(map[string]*ole.IDispatch),
	}, nil
}

// Initialize initializes the COM connection to Outlook
func (p *Provider) Initialize() error {
	p.mu.Lock()
	defer p.mu.Unlock()

	if p.initialized {
		return nil
	}

	// Lock this goroutine to the current OS thread for COM
	runtime.LockOSThread()
	
	// Initialize COM on this thread
	err := ole.CoInitializeEx(0, ole.COINIT_MULTITHREADED)
	if err != nil {
		// CoInitializeEx may return S_FALSE if already initialized on this thread
		// This is not an error, just means COM is already initialized
		if err.(*ole.OleError).Code() != 0x00000001 { // S_FALSE
			runtime.UnlockOSThread()
			return fmt.Errorf("failed to initialize COM: %w", err)
		}
	}

	// Get Outlook application
	unknown, err := oleutil.CreateObject("Outlook.Application")
	if err != nil {
		ole.CoUninitialize()
		runtime.UnlockOSThread()
		return fmt.Errorf("failed to create Outlook object: %w", err)
	}

	p.outlook, err = unknown.QueryInterface(ole.IID_IDispatch)
	if err != nil {
		unknown.Release()
		ole.CoUninitialize()
		runtime.UnlockOSThread()
		return fmt.Errorf("failed to query Outlook interface: %w", err)
	}
	unknown.Release()

	// Get MAPI namespace
	p.mapi = oleutil.MustGetProperty(p.outlook, "GetNamespace", "MAPI").ToIDispatch()

	p.initialized = true
	log.Println("Outlook COM provider initialized successfully")
	return nil
}

// Close closes the COM connection
func (p *Provider) Close() error {
	p.mu.Lock()
	defer p.mu.Unlock()

	if !p.initialized {
		return nil
	}

	// Release cached folders
	for _, folder := range p.folders {
		folder.Release()
	}
	p.folders = make(map[string]*ole.IDispatch)

	// Release MAPI and Outlook
	if p.mapi != nil {
		p.mapi.Release()
		p.mapi = nil
	}
	if p.outlook != nil {
		p.outlook.Release()
		p.outlook = nil
	}

	ole.CoUninitialize()
	runtime.UnlockOSThread()
	p.initialized = false
	log.Println("Outlook COM provider closed")
	return nil
}

// ensureCOMInitialized ensures COM is initialized on the current thread
// This must be called at the start of any public method that uses COM
func (p *Provider) ensureCOMInitialized() error {
	// Initialize COM on this thread if needed
	err := ole.CoInitializeEx(0, ole.COINIT_MULTITHREADED)
	if err != nil {
		// S_FALSE (0x00000001) means already initialized, which is fine
		if oleErr, ok := err.(*ole.OleError); ok && oleErr.Code() == 0x00000001 {
			return nil
		}
		// RPC_E_CHANGED_MODE means COM was initialized in a different mode
		// This is also acceptable - COM is initialized, just differently
		if oleErr, ok := err.(*ole.OleError); ok && oleErr.Code() == 0x80010106 {
			return nil
		}
		return fmt.Errorf("failed to initialize COM on thread: %w", err)
	}
	return nil
}

// GetFolder retrieves a folder by name, caching it for future use
func (p *Provider) GetFolder(folderName string) (*ole.IDispatch, error) {
	p.mu.Lock()
	defer p.mu.Unlock()

	if !p.initialized {
		return nil, fmt.Errorf("provider not initialized")
	}

	// Ensure COM is initialized on this thread
	if err := p.ensureCOMInitialized(); err != nil {
		return nil, err
	}

	return p.getFolder(folderName)
}

// getFolder is the internal unlocked version of GetFolder
// Must be called with p.mu held
func (p *Provider) getFolder(folderName string) (*ole.IDispatch, error) {
	// Check cache
	if folder, exists := p.folders[folderName]; exists {
		return folder, nil
	}

	// Get Inbox as reference
	inbox := oleutil.MustGetProperty(p.mapi, "GetDefaultFolder", 6).ToIDispatch() // 6 = olFolderInbox

	// If requesting Inbox, cache and return
	if folderName == "Inbox" || folderName == "" {
		p.folders["Inbox"] = inbox
		return inbox, nil
	}

	// Otherwise, get parent folders and search
	parent := oleutil.MustGetProperty(inbox, "Parent").ToIDispatch()
	folders := oleutil.MustGetProperty(parent, "Folders").ToIDispatch()
	defer folders.Release()

	// Try to get folder by name
	folder := oleutil.MustGetProperty(folders, "Item", folderName).ToIDispatch()
	p.folders[folderName] = folder

	return folder, nil
}

// GetEmails retrieves emails from a specific folder
func (p *Provider) GetEmails(folderName string, limit, offset int) ([]*models.Email, error) {
	p.mu.Lock()
	defer p.mu.Unlock()

	if !p.initialized {
		return nil, fmt.Errorf("provider not initialized")
	}

	// Ensure COM is initialized on this thread
	if err := p.ensureCOMInitialized(); err != nil {
		return nil, err
	}

	folder, err := p.getFolder(folderName) // Use internal unlocked method
	if err != nil {
		return nil, err
	}

	items := oleutil.MustGetProperty(folder, "Items").ToIDispatch()
	defer items.Release()

	// Sort by received time descending
	oleutil.MustCallMethod(items, "Sort", "[ReceivedTime]", true) // true = descending

	count := int(oleutil.MustGetProperty(items, "Count").Val)
	
	// Calculate range
	start := offset + 1 // COM is 1-indexed
	end := offset + limit
	if end > count {
		end = count
	}

	var emails []*models.Email
	for i := start; i <= end; i++ {
		item := oleutil.MustGetProperty(items, "Item", i).ToIDispatch()
		email := p.parseEmail(item)
		item.Release()
		
		if email != nil {
			emails = append(emails, email)
		}
	}

	return emails, nil
}

// GetEmailByID retrieves a specific email by its EntryID
func (p *Provider) GetEmailByID(entryID string) (*models.Email, error) {
	p.mu.Lock()
	defer p.mu.Unlock()

	if !p.initialized {
		return nil, fmt.Errorf("provider not initialized")
	}

	// Ensure COM is initialized on this thread
	if err := p.ensureCOMInitialized(); err != nil {
		return nil, err
	}

	// Protect against panic from MustGetProperty when email doesn't exist
	var item *ole.IDispatch
	var err error
	func() {
		defer func() {
			if r := recover(); r != nil {
				err = fmt.Errorf("email not found or EntryID invalid: %v", r)
			}
		}()
		item = oleutil.MustGetProperty(p.mapi, "GetItemFromID", entryID).ToIDispatch()
	}()
	
	if err != nil {
		return nil, err
	}
	if item == nil {
		return nil, fmt.Errorf("email not found with EntryID: %s", entryID)
	}
	defer item.Release()

	return p.parseEmail(item), nil
}

// parseEmail converts a COM email object to our Email model
func (p *Provider) parseEmail(item *ole.IDispatch) *models.Email {
	email := &models.Email{}

	// Get properties safely
	if prop := oleutil.MustGetProperty(item, "EntryID"); prop.Value() != nil {
		email.ID = prop.ToString()
	}

	if prop := oleutil.MustGetProperty(item, "Subject"); prop.Value() != nil {
		email.Subject = prop.ToString()
	}

	if prop := oleutil.MustGetProperty(item, "SenderEmailAddress"); prop.Value() != nil {
		email.Sender = prop.ToString()
	}

	if prop := oleutil.MustGetProperty(item, "Body"); prop.Value() != nil {
		body := prop.ToString()
		email.Body = body
		email.Content = body
	}

	if prop := oleutil.MustGetProperty(item, "ReceivedTime"); prop.Value() != nil {
		email.ReceivedTime = prop.Value().(time.Time)
		email.Date = email.ReceivedTime
	}

	if prop := oleutil.MustGetProperty(item, "UnRead"); prop.Value() != nil {
		email.IsRead = !prop.Value().(bool)
	}

	if prop := oleutil.MustGetProperty(item, "Attachments"); prop.Value() != nil {
		attachments := prop.ToIDispatch()
		count := int(oleutil.MustGetProperty(attachments, "Count").Val)
		email.HasAttachments = count > 0
		attachments.Release()
	}

	if prop := oleutil.MustGetProperty(item, "Importance"); prop.Value() != nil {
		importance := int(prop.Val)
		switch importance {
		case 0:
			email.Importance = "Low"
		case 1:
			email.Importance = "Normal"
		case 2:
			email.Importance = "High"
		default:
			email.Importance = "Normal"
		}
	}

	if prop := oleutil.MustGetProperty(item, "ConversationID"); prop.Value() != nil {
		email.ConversationID = prop.ToString()
	}

	// Get categories
	if prop := oleutil.MustGetProperty(item, "Categories"); prop.Value() != nil {
		categories := prop.ToString()
		if categories != "" {
			email.Categories = []string{categories}
		}
	}

	return email
}

// MarkAsRead marks an email as read
func (p *Provider) MarkAsRead(entryID string, read bool) error {
	p.mu.Lock()
	defer p.mu.Unlock()

	if !p.initialized {
		return fmt.Errorf("provider not initialized")
	}

	// Ensure COM is initialized on this thread
	if err := p.ensureCOMInitialized(); err != nil {
		return err
	}

	var item *ole.IDispatch
	var err error
	
	// Protect against panic when email doesn't exist
	func() {
		defer func() {
			if r := recover(); r != nil {
				err = fmt.Errorf("failed to mark as read, email not found: %v", r)
			}
		}()
		item = oleutil.MustGetProperty(p.mapi, "GetItemFromID", entryID).ToIDispatch()
	}()
	
	if err != nil {
		return err
	}
	if item == nil {
		return fmt.Errorf("email not found with EntryID: %s", entryID)
	}
	defer item.Release()

	oleutil.PutProperty(item, "UnRead", !read)
	oleutil.MustCallMethod(item, "Save")

	return nil
}

// MoveToFolder moves an email to a different folder
func (p *Provider) MoveToFolder(entryID, destinationFolder string) error {
	p.mu.Lock()
	defer p.mu.Unlock()

	if !p.initialized {
		return fmt.Errorf("provider not initialized")
	}

	// Ensure COM is initialized on this thread
	if err := p.ensureCOMInitialized(); err != nil {
		return err
	}

	var item *ole.IDispatch
	var err error
	
	// Protect against panic when email doesn't exist
	func() {
		defer func() {
			if r := recover(); r != nil {
				err = fmt.Errorf("failed to move, email not found: %v", r)
			}
		}()
		item = oleutil.MustGetProperty(p.mapi, "GetItemFromID", entryID).ToIDispatch()
	}()
	
	if err != nil {
		return err
	}
	if item == nil {
		return fmt.Errorf("email not found with EntryID: %s", entryID)
	}
	defer item.Release()

	targetFolder, err := p.getFolder(destinationFolder)
	if err != nil {
		return err
	}

	oleutil.MustCallMethod(item, "Move", targetFolder)
	return nil
}

// SetCategory sets the Outlook category for an email
func (p *Provider) SetCategory(entryID, category string) error {
	p.mu.Lock()
	defer p.mu.Unlock()

	if !p.initialized {
		return fmt.Errorf("provider not initialized")
	}

	// Ensure COM is initialized on this thread
	if err := p.ensureCOMInitialized(); err != nil {
		return err
	}

	var item *ole.IDispatch
	var err error
	
	// Protect against panic when email doesn't exist
	func() {
		defer func() {
			if r := recover(); r != nil {
				err = fmt.Errorf("failed to set category, email not found: %v", r)
			}
		}()
		item = oleutil.MustGetProperty(p.mapi, "GetItemFromID", entryID).ToIDispatch()
	}()
	
	if err != nil {
		return err
	}
	if item == nil {
		return fmt.Errorf("email not found with EntryID: %s", entryID)
	}
	defer item.Release()

	oleutil.PutProperty(item, "Categories", category)
	oleutil.MustCallMethod(item, "Save")

	return nil
}

// GetFolders retrieves list of email folders
func (p *Provider) GetFolders() ([]models.EmailFolder, error) {
	p.mu.Lock()
	defer p.mu.Unlock()

	if !p.initialized {
		return nil, fmt.Errorf("provider not initialized")
	}

	// Ensure COM is initialized on this thread
	if err := p.ensureCOMInitialized(); err != nil {
		return nil, err
	}

	inbox := oleutil.MustGetProperty(p.mapi, "GetDefaultFolder", 6).ToIDispatch()
	parent := oleutil.MustGetProperty(inbox, "Parent").ToIDispatch()
	folders := oleutil.MustGetProperty(parent, "Folders").ToIDispatch()
	defer folders.Release()

	count := int(oleutil.MustGetProperty(folders, "Count").Val)
	var result []models.EmailFolder

	for i := 1; i <= count; i++ {
		folder := oleutil.MustGetProperty(folders, "Item", i).ToIDispatch()
		
		name := oleutil.MustGetProperty(folder, "Name").ToString()
		items := oleutil.MustGetProperty(folder, "Items").ToIDispatch()
		
		totalCount := int(oleutil.MustGetProperty(items, "Count").Val)
		
		// Count unread items
		unreadCount := 0
		for j := 1; j <= totalCount; j++ {
			item := oleutil.MustGetProperty(items, "Item", j).ToIDispatch()
			if oleutil.MustGetProperty(item, "UnRead").Value().(bool) {
				unreadCount++
			}
			item.Release()
		}

		result = append(result, models.EmailFolder{
			Name:        name,
			UnreadCount: unreadCount,
			TotalCount:  totalCount,
			FolderPath:  name,
		})

		items.Release()
		folder.Release()
	}

	return result, nil
}

// GetConversationEmails retrieves all emails in a conversation
func (p *Provider) GetConversationEmails(conversationID string) ([]*models.Email, error) {
	p.mu.Lock()
	defer p.mu.Unlock()

	if !p.initialized {
		return nil, fmt.Errorf("provider not initialized")
	}

	// Ensure COM is initialized on this thread
	if err := p.ensureCOMInitialized(); err != nil {
		return nil, err
	}

	// Get Inbox
	inbox, err := p.getFolder("Inbox")
	if err != nil {
		return nil, err
	}

	items := oleutil.MustGetProperty(inbox, "Items").ToIDispatch()
	defer items.Release()

	count := int(oleutil.MustGetProperty(items, "Count").Val)
	var emails []*models.Email

	// Search for emails with matching conversation ID
	for i := 1; i <= count; i++ {
		item := oleutil.MustGetProperty(items, "Item", i).ToIDispatch()
		convID := oleutil.MustGetProperty(item, "ConversationID").ToString()
		
		if convID == conversationID {
			email := p.parseEmail(item)
			if email != nil {
				emails = append(emails, email)
			}
		}
		
		item.Release()
	}

	return emails, nil
}

// Category mappings - MUST match Python backend exactly
var InboxCategories = map[string]string{
	"required_personal_action": "Work Relevant",
	"team_action":              "Work Relevant",
	"fyi":                      "FYI",
	"newsletter":               "Newsletters",
}

var NonInboxCategories = map[string]string{
	"optional_event": "Optional Events",
	"job_listing":    "Job Listings",
	"spam_to_delete": "Spam",
}

// GetCategoryMappings returns all category to folder mappings
func GetCategoryMappings() []models.CategoryFolderMapping {
	var mappings []models.CategoryFolderMapping

	for cat, folder := range InboxCategories {
		mappings = append(mappings, models.CategoryFolderMapping{
			Category:     cat,
			FolderName:   folder,
			StaysInInbox: true,
		})
	}

	for cat, folder := range NonInboxCategories {
		mappings = append(mappings, models.CategoryFolderMapping{
			Category:     cat,
			FolderName:   folder,
			StaysInInbox: false,
		})
	}

	return mappings
}

// ApplyClassification applies AI classification to Outlook (move + category)
func (p *Provider) ApplyClassification(entryID, category string) error {
	p.mu.Lock()
	defer p.mu.Unlock()

	if !p.initialized {
		return fmt.Errorf("provider not initialized")
	}

	// Ensure COM is initialized on this thread
	if err := p.ensureCOMInitialized(); err != nil {
		return err
	}

	// Determine action based on category
	if folderName, isInbox := InboxCategories[category]; isInbox {
		// Stays in inbox, just set category
		return p.setCategory(entryID, folderName)
	} else if folderName, isNonInbox := NonInboxCategories[category]; isNonInbox {
		// Move to folder
		if err := p.moveToFolder(entryID, folderName); err != nil {
			return err
		}
		return p.setCategory(entryID, folderName)
	}

	return fmt.Errorf("unknown category: %s", category)
}

// Internal unlocked versions for use within locked contexts
func (p *Provider) setCategory(entryID, category string) error {
	var item *ole.IDispatch
	var err error
	
	// Protect against panic when email doesn't exist
	func() {
		defer func() {
			if r := recover(); r != nil {
				err = fmt.Errorf("failed to set category, email not found: %v", r)
			}
		}()
		item = oleutil.MustGetProperty(p.mapi, "GetItemFromID", entryID).ToIDispatch()
	}()
	
	if err != nil {
		return err
	}
	if item == nil {
		return fmt.Errorf("email not found with EntryID: %s", entryID)
	}
	defer item.Release()

	oleutil.PutProperty(item, "Categories", category)
	oleutil.MustCallMethod(item, "Save")
	return nil
}

func (p *Provider) moveToFolder(entryID, destinationFolder string) error {
	var item *ole.IDispatch
	var err error
	
	// Protect against panic when email doesn't exist
	func() {
		defer func() {
			if r := recover(); r != nil {
				err = fmt.Errorf("failed to move, email not found: %v", r)
			}
		}()
		item = oleutil.MustGetProperty(p.mapi, "GetItemFromID", entryID).ToIDispatch()
	}()
	
	if err != nil {
		return err
	}
	if item == nil {
		return fmt.Errorf("email not found with EntryID: %s", entryID)
	}
	defer item.Release()

	targetFolder, err := p.getFolder(destinationFolder)
	if err != nil {
		return err
	}

	oleutil.MustCallMethod(item, "Move", targetFolder)
	return nil
}
