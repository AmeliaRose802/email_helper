# TODO

- Aggressively clean up this code to reduce the lines and logical complexity.

First take a minute to understand the logical structure of the file so you know what is important and what isn't.

- Eliminate excessive error handling: 
Since this is non prod code, we don't want an intense level of error handling. Crashing is almost always preferable to continuing in a bad state. 

- Remove excess print statements when they record success.

- Don't keep multiple backup methods. Figure out what actually works and remove the others.

- In the review mode, include the AI generated summery too for faster review

- After the user applies suggestions in outlook, give them the option to load in another batch of suggestions, hiding the already reviewed emails. Include all emails reviewed during entire session in the summery

- Should be able to select a column to sort by

- Use some heruistic to retreve labeled examples similar to the current email from the modification suggestions. Then inject these examples into the prompt for few shot prompting.

- In the GUI, list emails by category for faster review

- For newsletters the paragraph summery should cover all newsletters not one paragraph per newsletter. The summaries of newsletters in the summery output is getting cut off. This may be related.

- Improve the colors and UI so the GUI looks less like accounting software from 2001

- The links included in tasks are nonsense/broken. Instead, can we include links to open the emails themselves in either outlook or the web version? Let me know the complexity of doing this

- If there are no items in a section, don't include it in the summery
