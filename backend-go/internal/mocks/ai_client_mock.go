package mocks

import (
	"context"
	"email-helper-backend/internal/models"
	"github.com/stretchr/testify/mock"
)

// MockAIClient is a mock implementation of the Azure OpenAI client
type MockAIClient struct {
	mock.Mock
}

func (m *MockAIClient) ClassifyEmail(ctx context.Context, subject, sender, content, userContext string) (*models.AIClassificationResponse, error) {
	args := m.Called(ctx, subject, sender, content, userContext)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.AIClassificationResponse), args.Error(1)
}

func (m *MockAIClient) ExtractActionItems(ctx context.Context, emailContent, userContext string) (*models.ActionItemResponse, error) {
	args := m.Called(ctx, emailContent, userContext)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.ActionItemResponse), args.Error(1)
}

func (m *MockAIClient) Summarize(ctx context.Context, emailContent, summaryType string) (*models.SummaryResponse, error) {
	args := m.Called(ctx, emailContent, summaryType)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.SummaryResponse), args.Error(1)
}

func (m *MockAIClient) CheckHealth(ctx context.Context) error {
	args := m.Called(ctx)
	return args.Error(0)
}
