# Changelog

All notable changes to this project will be documented here.

## [1.0.1] - 2025-07-14

### Changed
- Updated API in accordance to what his majesty `superadmin0` advised.
- Unified login failure handling across all modules
- Removed repetitive login prompts and fallback messages
- Eliminated emoji from CLI output for a cleaner terminal experience

### Fixed
- CLI no longer crashes when token/email/password is missing
- Graceful error output when not logged in
- API calls now avoided when not authenticated

---