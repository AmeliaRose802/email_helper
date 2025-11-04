package database

import (
	"database/sql"
	"fmt"
	"strings"
	"time"

	"email-helper-backend/internal/models"
)

// SaveEmail saves an email to the database
func SaveEmail(email *models.Email) error {
	db, err := GetDB()
	if err != nil {
		return err
	}

	query := `
		INSERT OR REPLACE INTO emails (
			id, user_id, subject, sender, recipient, content, received_date,
			category, ai_category, confidence, ai_confidence, ai_reasoning, one_line_summary,
			conversation_id, processed_at
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`

	_, err = db.Exec(query,
		email.ID,
		1, // Default user_id
		email.Subject,
		email.Sender,
		email.Recipient,
		email.Content,
		email.ReceivedTime,
		email.Category,
		email.AICategory,
		email.AIConfidence,
		email.AIConfidence,
		email.AIReasoning,
		email.OneLineSummary,
		email.ConversationID,
		time.Now(),
	)

	return err
}

// GetEmailByID retrieves an email by ID
func GetEmailByID(id string) (*models.Email, error) {
	db, err := GetDB()
	if err != nil {
		return nil, err
	}

	query := `
		SELECT id, subject, sender, recipient, content, received_date,
		       category, ai_category, ai_confidence, ai_reasoning, one_line_summary, conversation_id
		FROM emails
		WHERE id = ?
	`

	email := &models.Email{}
	err = db.QueryRow(query, id).Scan(
		&email.ID,
		&email.Subject,
		&email.Sender,
		&email.Recipient,
		&email.Content,
		&email.ReceivedTime,
		&email.Category,
		&email.AICategory,
		&email.AIConfidence,
		&email.AIReasoning,
		&email.OneLineSummary,
		&email.ConversationID,
	)

	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("email not found")
	}
	if err != nil {
		return nil, err
	}

	return email, nil
}

// GetEmails retrieves emails with pagination and filtering
func GetEmails(limit, offset int, category string) ([]*models.Email, int, error) {
	db, err := GetDB()
	if err != nil {
		return nil, 0, err
	}

	// Build query based on filters
	whereClause := "WHERE user_id = 1"
	args := []interface{}{}

	if category != "" {
		whereClause += " AND (ai_category = ? OR category = ?)"
		args = append(args, category, category)
	}

	// Count total
	countQuery := fmt.Sprintf("SELECT COUNT(*) FROM emails %s", whereClause)
	var total int
	err = db.QueryRow(countQuery, args...).Scan(&total)
	if err != nil {
		return nil, 0, err
	}

	// Get emails
	query := fmt.Sprintf(`
		SELECT id, subject, sender, recipient, content, received_date,
		       category, ai_category, ai_confidence, ai_reasoning, one_line_summary, conversation_id
		FROM emails
		%s
		ORDER BY received_date DESC
		LIMIT ? OFFSET ?
	`, whereClause)

	args = append(args, limit, offset)
	rows, err := db.Query(query, args...)
	if err != nil {
		return nil, 0, err
	}
	defer rows.Close()

	var emails []*models.Email
	for rows.Next() {
		email := &models.Email{}
		err := rows.Scan(
			&email.ID,
			&email.Subject,
			&email.Sender,
			&email.Recipient,
			&email.Content,
			&email.ReceivedTime,
			&email.Category,
			&email.AICategory,
			&email.AIConfidence,
			&email.AIReasoning,
			&email.OneLineSummary,
			&email.ConversationID,
		)
		if err != nil {
			return nil, 0, err
		}
		emails = append(emails, email)
	}

	return emails, total, nil
}

// SearchEmails searches emails by query string
func SearchEmails(query string, page, perPage int) ([]*models.Email, int, error) {
	db, err := GetDB()
	if err != nil {
		return nil, 0, err
	}

	offset := (page - 1) * perPage
	// Escape LIKE special characters (%, _) to treat them literally
	escaped := strings.ReplaceAll(query, "%", "\\%")
	escaped = strings.ReplaceAll(escaped, "_", "\\_")
	searchPattern := "%" + escaped + "%"

	// Count total
	countQuery := `
		SELECT COUNT(*)
		FROM emails
		WHERE user_id = 1
		  AND (subject LIKE ? OR sender LIKE ? OR content LIKE ?)
	`
	var total int
	err = db.QueryRow(countQuery, searchPattern, searchPattern, searchPattern).Scan(&total)
	if err != nil {
		return nil, 0, err
	}

	// Get emails
	searchQuery := `
		SELECT id, subject, sender, recipient, content, received_date,
		       category, ai_category, ai_confidence, ai_reasoning, one_line_summary, conversation_id
		FROM emails
		WHERE user_id = 1
		  AND (subject LIKE ? OR sender LIKE ? OR content LIKE ?)
		ORDER BY received_date DESC
		LIMIT ? OFFSET ?
	`

	rows, err := db.Query(searchQuery, searchPattern, searchPattern, searchPattern, perPage, offset)
	if err != nil {
		return nil, 0, err
	}
	defer rows.Close()

	var emails []*models.Email
	for rows.Next() {
		email := &models.Email{}
		err := rows.Scan(
			&email.ID,
			&email.Subject,
			&email.Sender,
			&email.Recipient,
			&email.Content,
			&email.ReceivedTime,
			&email.Category,
			&email.AICategory,
			&email.AIConfidence,
			&email.AIReasoning,
			&email.OneLineSummary,
			&email.ConversationID,
		)
		if err != nil {
			return nil, 0, err
		}
		emails = append(emails, email)
	}

	return emails, total, nil
}

// UpdateEmailClassification updates the category of an email
func UpdateEmailClassification(id, category string) error {
	db, err := GetDB()
	if err != nil {
		return err
	}

	query := "UPDATE emails SET category = ? WHERE id = ?"
	_, err = db.Exec(query, category, id)
	return err
}

// GetConversationEmails retrieves all emails in a conversation thread
func GetConversationEmails(conversationID string) ([]*models.Email, error) {
	if conversationID == "" {
		return nil, fmt.Errorf("conversation ID cannot be empty")
	}
	
	db, err := GetDB()
	if err != nil {
		return nil, err
	}

	query := `
		SELECT id, subject, sender, recipient, content, received_date,
		       category, ai_category, ai_confidence, ai_reasoning, one_line_summary, conversation_id
		FROM emails
		WHERE conversation_id = ?
		ORDER BY received_date ASC
	`

	rows, err := db.Query(query, conversationID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var emails []*models.Email
	for rows.Next() {
		email := &models.Email{}
		err := rows.Scan(
			&email.ID,
			&email.Subject,
			&email.Sender,
			&email.Recipient,
			&email.Content,
			&email.ReceivedTime,
			&email.Category,
			&email.AICategory,
			&email.AIConfidence,
			&email.AIReasoning,
			&email.OneLineSummary,
			&email.ConversationID,
		)
		if err != nil {
			return nil, err
		}
		emails = append(emails, email)
	}

	return emails, nil
}

// GetEmailStats retrieves statistics about emails
func GetEmailStats(limit int) (map[string]interface{}, error) {
	db, err := GetDB()
	if err != nil {
		return nil, err
	}

	stats := make(map[string]interface{})

	// Total emails
	var total int
	err = db.QueryRow("SELECT COUNT(*) FROM emails WHERE user_id = 1").Scan(&total)
	if err != nil {
		return nil, err
	}
	stats["total_emails"] = total

	// Emails by category
	categoryQuery := `
		SELECT COALESCE(ai_category, 'uncategorized') as cat, COUNT(*) as count
		FROM emails
		WHERE user_id = 1
		GROUP BY ai_category
	`
	rows, err := db.Query(categoryQuery)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	emailsByCategory := make(map[string]int)
	for rows.Next() {
		var category string
		var count int
		if err := rows.Scan(&category, &count); err != nil {
			return nil, err
		}
		emailsByCategory[category] = count
	}
	stats["emails_by_category"] = emailsByCategory

	// Top senders
	senderQuery := `
		SELECT sender, COUNT(*) as count
		FROM emails
		WHERE user_id = 1
		GROUP BY sender
		ORDER BY count DESC
		LIMIT ?
	`
	rows, err = db.Query(senderQuery, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	emailsBySender := make(map[string]int)
	for rows.Next() {
		var sender string
		var count int
		if err := rows.Scan(&sender, &count); err != nil {
			return nil, err
		}
		emailsBySender[sender] = count
	}
	stats["emails_by_sender"] = emailsBySender

	return stats, nil
}

// GetAccuracyStats retrieves AI classification accuracy statistics
func GetAccuracyStats() (map[string]interface{}, error) {
	db, err := GetDB()
	if err != nil {
		return nil, err
	}

	stats := make(map[string]interface{})

	// Total classified emails (only count emails with both AI and user categories that are not empty)
	var totalClassified int
	err = db.QueryRow("SELECT COUNT(*) FROM emails WHERE ai_category IS NOT NULL AND ai_category != '' AND category IS NOT NULL AND category != '' AND user_id = 1").Scan(&totalClassified)
	if err != nil {
		return nil, err
	}
	stats["total_classified"] = totalClassified

	// User-corrected classifications
	var corrected int
	err = db.QueryRow("SELECT COUNT(*) FROM emails WHERE category IS NOT NULL AND category != '' AND category != ai_category AND user_id = 1").Scan(&corrected)
	if err != nil {
		return nil, err
	}
	stats["user_corrected"] = corrected

	// Calculate accuracy
	if totalClassified > 0 {
		accuracy := float64(totalClassified-corrected) / float64(totalClassified) * 100
		stats["accuracy_percentage"] = accuracy
	} else {
		stats["accuracy_percentage"] = 0.0
	}

	// Average confidence
	var avgConfidence sql.NullFloat64
	err = db.QueryRow("SELECT AVG(ai_confidence) FROM emails WHERE ai_confidence IS NOT NULL AND user_id = 1").Scan(&avgConfidence)
	if err != nil {
		return nil, err
	}
	if avgConfidence.Valid {
		stats["average_confidence"] = avgConfidence.Float64
	} else {
		stats["average_confidence"] = 0.0
	}

	return stats, nil
}
