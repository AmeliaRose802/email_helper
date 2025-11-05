package middleware

import (
	"fmt"
	"time"

	"github.com/gin-gonic/gin"
)

// Version information (will be set at build time)
var (
	Version   = "dev"
	GitCommit = "unknown"
	BuildTime = "unknown"
)

// SetVersion sets the version information for the API
func SetVersion(version, commit, buildTime string) {
	if version != "" {
		Version = version
	}
	if commit != "" {
		GitCommit = commit
	}
	if buildTime != "" {
		BuildTime = buildTime
	}
}

// StandardHeaders adds standard API headers to all responses
func StandardHeaders() gin.HandlerFunc {
	return func(c *gin.Context) {
		// Add API version header
		c.Header("X-API-Version", Version)
		
		// Add build information
		c.Header("X-Git-Commit", GitCommit)
		
		// Add standard security headers
		c.Header("X-Content-Type-Options", "nosniff")
		c.Header("X-Frame-Options", "DENY")
		
		// CORS headers are handled by separate middleware if needed
		
		c.Next()
	}
}

// PaginationHeaders adds pagination metadata headers for list responses
func PaginationHeaders(total, page, pageSize int, hasMore bool) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Header("X-Pagination-Total", fmt.Sprintf("%d", total))
		c.Header("X-Pagination-Page", fmt.Sprintf("%d", page))
		c.Header("X-Pagination-Page-Size", fmt.Sprintf("%d", pageSize))
		if hasMore {
			c.Header("X-Pagination-Has-More", "true")
		} else {
			c.Header("X-Pagination-Has-More", "false")
		}
		c.Next()
	}
}

// AddPaginationHeaders adds pagination headers to the current response
func AddPaginationHeaders(c *gin.Context, total, page, pageSize int, hasMore bool) {
	c.Header("X-Pagination-Total", fmt.Sprintf("%d", total))
	c.Header("X-Pagination-Page", fmt.Sprintf("%d", page))
	c.Header("X-Pagination-Page-Size", fmt.Sprintf("%d", pageSize))
	if hasMore {
		c.Header("X-Pagination-Has-More", "true")
	} else {
		c.Header("X-Pagination-Has-More", "false")
	}
}

// DeprecationWarning adds deprecation headers to responses
func DeprecationWarning(message, sunsetDate, replacementEndpoint string) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Header("X-Deprecation-Warning", "true")
		if message != "" {
			c.Header("X-Deprecation-Message", message)
		}
		if sunsetDate != "" {
			c.Header("X-Sunset", sunsetDate)
		}
		if replacementEndpoint != "" {
			c.Header("X-Replacement-Endpoint", replacementEndpoint)
		}
		c.Next()
	}
}

// ResponseTimer middleware to track and log response times
func ResponseTimer() gin.HandlerFunc {
	return func(c *gin.Context) {
		startTime := time.Now()
		
		// Process request
		c.Next()
		
		// Calculate response time
		duration := time.Since(startTime)
		responseTimeMs := duration.Milliseconds()
		
		// Add response time header
		c.Header("X-Response-Time-Ms", fmt.Sprintf("%d", responseTimeMs))
		
		// Log slow requests (>1000ms)
		if responseTimeMs > 1000 {
			c.Set("slow_request", true)
			// Log warning for slow requests
			// TODO: Add proper logging
		}
	}
}
