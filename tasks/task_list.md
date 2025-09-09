# TODO

Improvements:

- We should also include links to open the emails themselves in either outlook or the web version? Let me know the complexity of doing this. Store the entry ID and use it to create a link to the relevant email.

- Record all human accepted suggestions which were applied to outlook, not just the changed ones in the review view. This will allow us to have better data for fine tuning.

- Use some heruistic to retreve labeled examples similar to the current email from the modification suggestions. Then inject these examples into the prompt for few shot prompting.

- ✅ The ai_deleted section should move out of the inbox - **COMPLETED**: Moved 'spam_to_delete' category from inbox_categories to non_inbox_categories so AI-deleted emails are placed outside the inbox at the mail root level