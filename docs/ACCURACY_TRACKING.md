# Email Classification Accuracy Tracking

## Overview

The email management system now tracks AI classification accuracy by monitoring how many emails users reclassify. This helps monitor system performance over time and identify areas for improvement.

## How It Works

### 1. **Session Tracking**
- When you run the email processor, accuracy tracking begins automatically
- The system counts total emails processed in each session
- User corrections are tracked in real-time

### 2. **Accuracy Calculation**
```
Accuracy Rate = (Emails Not Corrected / Total Emails) × 100
```

### 3. **Persistent Storage**
- Accuracy data is stored in `runtime_data/user_feedback/accuracy_tracking.csv`
- Summary metrics are saved in `runtime_data/user_feedback/accuracy_summary.json`
- User corrections continue to be logged in `suggestion_modifications.csv`

## Features

### 📊 **Session Summary**
After each email processing session, you'll see:
- Total emails processed
- Number of user corrections
- Accuracy rate for the session
- Session duration
- Most corrected categories

### 📈 **Trend Analysis**
- Average accuracy over time periods
- Best/worst accuracy rates
- Improvement trends (improving/declining/stable)
- Problem category identification

### 📋 **Accuracy Report Menu**
New menu option (4) in the editing interface:
```
4. 📊 Show accuracy report
```

### 🖥️ **Standalone Report**
Run detailed accuracy analysis anytime:
```bash
python show_accuracy_report.py [days_back]
```

Examples:
```bash
python show_accuracy_report.py          # Last 30 days (default)
python show_accuracy_report.py 7        # Last 7 days
python show_accuracy_report.py 90       # Last 90 days
```

## Data Files Created

1. **`runtime_data/user_feedback/accuracy_tracking.csv`**
   - Session-by-session accuracy metrics
   - Timestamps, email counts, accuracy rates
   - Error counts and processing duration

2. **`runtime_data/user_feedback/accuracy_summary.json`**
   - Quick summary of latest accuracy metrics
   - Problem categories and improvement trends

3. **Existing files enhanced:**
   - `suggestion_modifications.csv` - Used for category analysis
   - `ai_learning_feedback.csv` - Includes accuracy finalization

## Understanding the Report

### 📊 **Accuracy Metrics**
- **Current accuracy**: Latest session accuracy
- **Average accuracy**: Mean across selected time period
- **Best/Worst accuracy**: Highest and lowest rates recorded

### 🎯 **Trend Analysis**
- **📈 Improving**: Accuracy is getting better over time
- **📉 Declining**: Accuracy is dropping (investigate recent changes)
- **➡️ Stable**: Accuracy remains consistent

### 🔍 **Category Analysis**
- **Most corrected categories**: Where AI makes frequent mistakes
- **User preferences**: Categories users select most often
- Helps identify patterns in corrections

### 💡 **Recommendations**
Based on accuracy levels:
- **90%+**: Excellent performance
- **80-89%**: Good, minor tuning suggested
- **70-79%**: Moderate, review classification rules
- **<70%**: Needs attention, update prompts/examples

## Using the Data

### **For Developers**
- Monitor accuracy trends after code changes
- Identify which categories need better training examples
- Track performance improvements from prompt updates

### **For Users**
- Understand how well the AI is learning from corrections
- See which email types are most challenging
- Track system improvement over time

### **For System Optimization**
- Focus improvement efforts on most problematic categories
- Adjust classification rules based on correction patterns
- Update prompts with examples from frequently corrected emails

## Example Output

```
📊 AI CLASSIFICATION ACCURACY REPORT
============================================================
📅 Period: 2024-09-01 to 2024-09-08
🔄 Total runs: 5
📧 Emails processed: 127
✏️  User corrections: 23

📈 ACCURACY METRICS:
   Current accuracy: 85.2%
   Average accuracy: 81.9%
   Best accuracy: 92.1%
   Worst accuracy: 70.4%

🎯 TREND ANALYSIS:
   Overall trend: 📈 Improving

🔍 MOST CORRECTED CATEGORIES:
   • Required Personal Action: 8 corrections
   • Work Relevant: 6 corrections
   • Spam To Delete: 4 corrections

💡 RECOMMENDATIONS:
   ✅ Good accuracy. Consider fine-tuning based on most corrected categories.
   📈 Great! Accuracy is improving over time.
   🎯 Focus improvement efforts on 'Required Personal Action' category.
```

## Next Steps

1. **Run the system** and make corrections to generate accuracy data
2. **Check accuracy reports** regularly to monitor performance  
3. **Focus improvements** on categories with frequent corrections
4. **Track trends** after making changes to prompts or rules

The accuracy tracking system will help you understand and improve the AI's performance over time!
