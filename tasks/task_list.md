# TODO

- ✅ **FIXED**: KeyError 'newsletter' during email processing - missing keys in _reset_data_storage() method
  - ✅ Added 'fyi' and 'newsletter' keys to _reset_data_storage() method in EmailProcessor
  - ✅ Verified both categories now work properly without KeyError exceptions
  - ✅ Confirmed GUI integration uses get_available_categories() which includes new categories

- Delete unused files. Clean up unused code.

- ✅ **COMPLETED**: Allow the user to complete the entire flow within the UI:
  - ✅ Created unified GUI with tabbed workflow (Process → Edit → Summary)
  - ✅ Added email count selection with predefined options (25, 50, 100, 200) plus custom input
  - ✅ Implemented real-time email processing with live progress updates and cancellation
  - ✅ Integrated email editing interface with category changes and explanations
  - ✅ Added in-app summary generation with text preview and browser opening
  - ✅ Created seamless workflow: Select emails → Watch processing → Edit classifications → Generate summary → View results
  - ✅ All functionality available in single interface - no command line switching required
  - ✅ Background processing with detailed progress logging and error handling
  - ✅ Full conversation thread support with participant tracking
  - ✅ Session management with ability to start new processing batches

- ✅ **COMPLETED**: Add a new FIY category for items that are notices. The summery of these items should be included in the summery in a new section.
  - ✅ Added FYI category to email classifier system
  - ✅ Created `fyi_summary.prompty` for generating concise bullet point summaries
  - ✅ Updated email processor to handle FYI emails and generate summaries
  - ✅ Added FYI notices section to summary generator (displays as bullet points)
  - ✅ Updated HTML template to include FYI notices section
  - ✅ FYI notices are included in the summary with sender attribution

- ✅ **COMPLETED**: Add a new category called newsletters. A 1 paragraph summery of the newsletters I got should be included in the email summery.
  - ✅ Added NEWSLETTER category to email classifier system  
  - ✅ Created `newsletter_summary.prompty` for generating paragraph summaries
  - ✅ Updated email processor to handle newsletter emails and generate summaries
  - ✅ Added newsletters section to summary generator (paragraph format)
  - ✅ Updated HTML template to include newsletters summary section
  - ✅ Multiple newsletters are combined into comprehensive highlights
  - ✅ Single newsletters display with full context and formatting

- After the user applies suggestions in outlook, give them the option to load in another batch of suggestions, hiding the already reviewed emails. Include all emails reviewed during entire session in the summery

- In the GUI, list emails by category for faster review

- For newsletters the paragraph summery should cover all newsletters not one paragraph per newsletter

- ✅ **COMPLETED**: When an email shows up, check all emails in inbox for thread matches and include them. Thread emails may be in older emails that are not part of the emails currently being reviewed. If possible, use outlook APIs and metadata to determine threads rather then just subject
  - ✅ Replaced subject-based thread grouping with Outlook's native ConversationID API
  - ✅ Added `get_emails_with_full_conversations()` method that searches up to 30 days back for related emails
  - ✅ Uses ConversationID to find all emails in a conversation thread, including older ones
  - ✅ Enhanced thread context building with full conversation history
  - ✅ Updated email processing to include full conversation context in AI analysis
  - ✅ Fixed single email handling to ensure emails without threads are still processed
  - ✅ Updated categorization batch processing to handle new thread data structure
  - ✅ Threads now properly include all related emails regardless of when they were received

- ✅ **COMPLETED**: Include classification in the GUI view as a column
  - ✅ GUI displays "AI Category" as the third column in the email list
  - ✅ Shows human-readable category names (e.g., "Team Action", "Required Personal Action")
  - ✅ Category column is properly populated for both single emails and conversation threads
  - ✅ Category column is editable through the details panel dropdown
  - ✅ Category updates are reflected in the GUI immediately after changes

- Improve the colors and UI so the GUI looks less like accounting software from 2001

- Since the GUI is great, let's remove the command line based option

- The links included in tasks are nonsense/broken. Instead, can we include links to open the emails themselves in either outlook or the web version? Let me know the complexity of doing this

- If there are no items in a section, don't include it in the summery
