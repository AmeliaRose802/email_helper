# TODO

- ✅ **COMPLETED**: Create the summaries under a new folder created at runtime called runtime_data/ai_summaries. Add this entire folder to the git ignore.
  - ✅ Updated `summary_generator.py` to save HTML summaries to `runtime_data/ai_summaries/`
  - ✅ Added `runtime_data/` to `.gitignore` to exclude all runtime generated files
  - ✅ Moved existing HTML summary files to the new location
  - ✅ Removed duplicate HTML file patterns from `.gitignore` (now covered by runtime_data/)

- Add a new FIY category. The summery of these items should be included in the summery in a new section.

- If there are no items in a section, don't include it in the summery

- The links included in tasks are nonsense/broken. Instead, can we include links to open the emails themselves in either outlook or the web version? Let me know the complexity of doing this

- Delete unused files. Clean up unused code.

- ✅ **COMPLETED**: Move the user specific personal data about the job etc to a separate directory. List these files in the git ignore. Add info to the readme explaining the format for these files so users can insert their own rules.
  - ✅ Created `user_specific_data/` directory structure
  - ✅ Updated `ai_processor.py` paths to use new location
  - ✅ Added `user_specific_data/` to `.gitignore`
  - ✅ Created template files and README documentation
  - ✅ Added setup script for easy initialization

- ✅ **COMPLETED**: Move info that is specific to the user out of the email_classifer_system.promply. Instead move this data into a separate markdown file and inject it so that it can be kept confidential. Update the readme to reflect the need for this.



- ✅ **COMPLETED**: Remove direct references to the users alias from prompt files. Instead pass this in as an argument to the prompts so it can be kept private and can support multiple users. It can be read from a persistent file stored locally
  - ✅ Created `username.txt` in user_specific_data directory
  - ✅ Updated `ai_processor.py` to load username and inject it into all prompts
  - ✅ Updated all prompty files to accept username as input parameter
  - ✅ Replaced hardcoded "ameliapayne" references with {{username}} template
  - ✅ Updated setup script to configure username during installation
  - ✅ Added username.txt.template for new users

- Show accuracy rate based on how many user reclassifies. Store the accuracy rate for each run so we can persistently across runs so we can monitor it over time. We want to be able to track how changes to the meta prompts impact accuracy rate.

- Make a GUI for viewing and modifying suggestions. Suggestions should be visble. The user should be able to change the classification using a drop down menu.


