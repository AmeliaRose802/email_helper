# TODO

- Delete unused files. Clean up unused code.

# TODO

- Delete unused files. Clean up unused code.

- ✅ **COMPLETED**: Show accuracy rate based on how many emails user reclassifies. Store the accuracy rate in runtime_data for each run so we can persistently across runs so we can monitor it over time. We want to be able to track how changes impact accuracy rate.
  - ✅ Created `AccuracyTracker` class for comprehensive accuracy monitoring
  - ✅ Added session tracking to AI processor with start/finalize methods
  - ✅ Integrated accuracy calculation based on user corrections
  - ✅ Added persistent storage in `runtime_data/user_feedback/accuracy_tracking.csv`
  - ✅ Created accuracy report menu option in user interface
  - ✅ Built standalone accuracy report script (`show_accuracy_report.py`)
  - ✅ Added trend analysis (improving/declining/stable) over time periods
  - ✅ Added category analysis to identify problem areas
  - ✅ Added session summaries showing accuracy after each run
  - ✅ Created comprehensive documentation (`docs/ACCURACY_TRACKING.md`)
  - ✅ Successfully tested accuracy calculation and report generation

- Make a GUI for viewing and modifying suggestions. Please think though how you'll do this first.

The UI should show a list of the AI suggestions. Users should be able to reclassify a suggestion using a drop down menu. This can be done in a desktop app window launched by the python script.

- The links included in tasks are nonsense/broken. Instead, can we include links to open the emails themselves in either outlook or the web version? Let me know the complexity of doing this

- ✅ **COMPLETED**: classification_rules.md does not appear to contain any internal info. It should go back into the promptly file email_classifier_system.prompty.
  - ✅ Integrated classification rules directly into `email_classifier_system.prompty`
  - ✅ Removed external `classification_rules.md` file dependency
  - ✅ Updated `ai_processor.py` to remove classification_rules file loading
  - ✅ Simplified prompty interface by removing classification_rules input parameter
  - ✅ Updated test files to reflect the consolidated structure

- Add a new FIY category. The summery of these items should be included in the summery in a new section.

- If there are no items in a section, don't include it in the summery


