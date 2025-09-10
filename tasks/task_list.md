# TODO

Improvements:

- ✅ **Mark Done button functionality fix** - Fixed issue where "✅ Mark Done" buttons in summary view weren't working because current batch tasks didn't have `task_id` fields. Updated `get_comprehensive_summary()` in task_persistence.py to ensure all tasks (both outstanding and current) include proper task_id values for completion tracking. **ADDITIONAL FIXES**: Fixed Text widget state issue - kept widget in NORMAL state with click handlers instead of DISABLED state that prevented tag click events. Also fixed tag parsing logic to correctly extract task_id from specific tags rather than generic "complete_button" tag. **FINAL SOLUTION**: Replaced problematic text-tag-based clickable buttons with embedded `tk.Button` widgets using `window_create()` for reliable click detection and proper button functionality across all task categories (Required Actions, Optional Actions, Job Listings).

- ✅ **AI classification markdown cleanup** - Fixed issue where AI classifier was returning category names with markdown asterisks (e.g., `**fyi**` instead of `fyi`), causing those items to not be properly categorized or counted in Outlook folder distribution. Added cleanup logic to strip asterisks from AI responses in both `classify_email()` and `classify_email_improved()` methods.

- ✅ **FYI categorization case sensitivity fix** - Fixed issue where items marked as "FYI" (uppercase) instead of "fyi" (lowercase) were not being counted correctly in the Outlook categorization folder distribution. Made category counting and folder mapping case-insensitive across both unified_gui.py and outlook_manager.py to handle all case variations ('fyi', 'FYI', 'Fyi').

- ✅ **Holistic analysis JSON parsing error fix** - Fixed "Unterminated string starting at: line 70 column 25 (char 4664)" error by adding robust JSON parsing with repair attempts. System now gracefully handles malformed AI responses and continues processing normally.

- ✅ **Manual task completion in summary view** - Added inline "✅ Mark Done" buttons for each task item directly in the summary display, allowing users to mark individual tasks as completed without opening a separate dialog. **FIXED**: Converted from embedded ttk.Button widgets to styled clickable text tags for proper appearance and functionality in disabled text widgets.

- ✅ Use AI and threads to determine if a team action has already been completed by someone else (look for replies providing info or other indications that it is finished) and to mark it as complete if so

- We should also include links to open the emails themselves in either outlook or the web version? Let me know the complexity of doing this. Store the entry ID and use it to create a link to the relevant email.

- ✅ Record all human accepted suggestions which were applied to outlook, not just the changed ones in the review view. This will allow us to have better data for fine tuning. - **COMPLETED**: Added `record_accepted_suggestions()` method that captures ALL applied suggestions (both user-modified and accepted as-is) with complete metadata for AI fine-tuning including initial vs final classifications, modification reasons, processing notes, and email content.

- Use some heruistic to retreve labeled examples similar to the current email from the modification suggestions. Then inject these examples into the prompt for few shot prompting.

- ✅ The ai_deleted section should move out of the inbox - **COMPLETED**: Moved 'spam_to_delete' category from inbox_categories to non_inbox_categories so AI-deleted emails are placed outside the inbox at the mail root level

- # When user marks task as complete, move associated email to a done folder (outside the inbox) in outlook
   - Make sure to create the done folder
  - You will need to record a list of entityIDs for emails associated with each task. Keep in mind that multiple emails may be associated with the same task
  - When the user marks a task as done, move it to the done folder. THis should not be under the inbox.
  


- Identify the types of tasks that I am requested to do in my inbox that an agent might be able to handle. Add in sub agents to handle these tasks

- Include date email was sent in task listing

- Fyi's should expire after some amount of time

- Use multiple input sources (IE, Teams) to gather tasks and understand their status

- Add buttons to clear all FYI's or all newsletters

- Links in tasks should have descriptions 

- Show running log of accuracy rate in app

- Let me directly go to the task tab without always having to classify emails first

Ideas:

Not all errors matter equally. Missing a Required Action is worse than misclassifying an FYI. Use asymmetric confidence thresholds (e.g., only auto-approve FYIs if >90% confident, but always review Required Actions).

- Allow the holistic review to check the summery lists and remove emails that are already covered by an existing task

