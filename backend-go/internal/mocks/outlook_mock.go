package mocks

import (
	"email-helper-backend/internal/models"
	"github.com/stretchr/testify/mock"
)

// MockOutlookProvider is a mock implementation of the Outlook provider
type MockOutlookProvider struct {
	mock.Mock
}

func (m *MockOutlookProvider) Initialize() error {
	args := m.Called()
	return args.Error(0)
}

func (m *MockOutlookProvider) Close() error {
	args := m.Called()
	return args.Error(0)
}

func (m *MockOutlookProvider) GetEmails(folder string, limit, offset int) ([]*models.Email, error) {
	args := m.Called(folder, limit, offset)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*models.Email), args.Error(1)
}

func (m *MockOutlookProvider) GetEmailByID(id string) (*models.Email, error) {
	args := m.Called(id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.Email), args.Error(1)
}

func (m *MockOutlookProvider) MarkAsRead(id string, read bool) error {
	args := m.Called(id, read)
	return args.Error(0)
}

func (m *MockOutlookProvider) MoveToFolder(id, folder string) error {
	args := m.Called(id, folder)
	return args.Error(0)
}

func (m *MockOutlookProvider) ApplyClassification(id, category string) error {
	args := m.Called(id, category)
	return args.Error(0)
}

func (m *MockOutlookProvider) GetFolders() ([]models.EmailFolder, error) {
	args := m.Called()
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]models.EmailFolder), args.Error(1)
}

func (m *MockOutlookProvider) GetConversationEmails(conversationID string) ([]*models.Email, error) {
	args := m.Called(conversationID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*models.Email), args.Error(1)
}

func (m *MockOutlookProvider) SetCategory(entryID, category string) error {
	args := m.Called(entryID, category)
	return args.Error(0)
}
