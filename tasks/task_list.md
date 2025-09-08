# TODO

- Show accuracy rate based on how many emails user reclassifies. Store the accuracy rate in runtime_data for each run so we can persistently across runs so we can monitor it over time. We want to be able to track how changes impact accuracy rate.

# TODO



- ✅ **COMPLETED**: classification_rules.md does not appear to contain any internal info. It should go back into the promptly file email_classifier_system.prompty.
  - ✅ Integrated classification rules directly into `email_classifier_system.prompty`
  - ✅ Removed external `classification_rules.md` file dependency
  - ✅ Updated `ai_processor.py` to remove classification_rules file loading
  - ✅ Simplified prompty interface by removing classification_rules input parameter
  - ✅ Updated test files to reflect the consolidated structure


- Add a new FIY category. The summery of these items should be included in the summery in a new section.

- If there are no items in a section, don't include it in the summery

- The links included in tasks are nonsense/broken. Instead, can we include links to open the emails themselves in either outlook or the web version? Let me know the complexity of doing this

- Delete unused files. Clean up unused code.



- Make a GUI for viewing and modifying suggestions. Suggestions should be visble. The user should be able to change the classification using a drop down menu.
