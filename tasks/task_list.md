# TODO

BUGS:

- Render emails correctly in review pane so that they are easier to read. We don't need to have complete formatting or show images but links should at least be linked so they don't make it hard to read the email.

- When review pane first opens, automatically load in first email

- The links included in tasks are often to images. We should not return broken links or links to images. 

- However we should also include links to open the emails themselves in either outlook or the web version? Let me know the complexity of doing this. Store the entry ID and use it to create a link to the relevant email.

Improvements:

- Record all human accepted suggestions, not just the changed ones in the review view. This will allow us to have better data for fine tuning.

- In the review mode, include the AI generated summery too for faster review

- Should be able to select a column to sort by

- Use some heruistic to retreve labeled examples similar to the current email from the modification suggestions. Then inject these examples into the prompt for few shot prompting.

- In the GUI, list emails by category for faster review

- For newsletters the paragraph summery should cover all newsletters not one paragraph per newsletter. The summaries of newsletters in the summery output is getting cut off. This may be related.

- Improve the colors and UI so the GUI looks less like accounting software from 2001

- If there are no items in a section, don't include it in the summery

- SUmmery should be opened in app rather then directing us to the browser
