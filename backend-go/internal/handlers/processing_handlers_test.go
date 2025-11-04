package handlers

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
)

// Processing handlers are all stubs that return 501 Not Implemented
// These tests verify the stub behavior

func TestStartProcessingNotImplemented(t *testing.T) {
	router := setupTestRouter()
	router.POST("/processing/start", StartProcessing)

	req, _ := http.NewRequest("POST", "/processing/start", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusNotImplemented, w.Code)
}

func TestGetProcessingStatusNotImplemented(t *testing.T) {
	router := setupTestRouter()
	router.GET("/processing/:id/status", GetProcessingStatus)

	req, _ := http.NewRequest("GET", "/processing/123/status", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusNotImplemented, w.Code)
}

func TestGetPipelineJobsNotImplemented(t *testing.T) {
	router := setupTestRouter()
	router.GET("/processing/jobs", GetPipelineJobs)

	req, _ := http.NewRequest("GET", "/processing/jobs", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusNotImplemented, w.Code)
}

func TestCancelProcessingNotImplemented(t *testing.T) {
	router := setupTestRouter()
	router.POST("/processing/:id/cancel", CancelProcessing)

	req, _ := http.NewRequest("POST", "/processing/123/cancel", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusNotImplemented, w.Code)
}

func TestGetProcessingStatsNotImplemented(t *testing.T) {
	router := setupTestRouter()
	router.GET("/processing/stats", GetProcessingStats)

	req, _ := http.NewRequest("GET", "/processing/stats", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusNotImplemented, w.Code)
}

func TestWebSocketPipelineNotImplemented(t *testing.T) {
	router := setupTestRouter()
	router.GET("/processing/ws/:id", WebSocketPipeline)

	req, _ := http.NewRequest("GET", "/processing/ws/123", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusNotImplemented, w.Code)
}

func TestWebSocketGeneralNotImplemented(t *testing.T) {
	router := setupTestRouter()
	router.GET("/ws", WebSocketGeneral)

	req, _ := http.NewRequest("GET", "/ws", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusNotImplemented, w.Code)
}
