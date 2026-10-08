# Contributing to Seraphine Translations

Thank you for your interest in helping with Seraphine's translations! This guide will help you understand how to contribute translations to the project.

## Translation Files

Seraphine uses Qt's translation system (`.ts` files) for UI translations. The translation files are located in:

- UI Translations: `app/resource/i18n/Seraphine.{locale}.ts`

Currently supported languages:
- Chinese Simplified (zh_CN)

> Only Chinese Simplified is shipped. The Python source strings are English, and the Chinese UI text
> comes from the compiled `Seraphine.zh_CN.qm` — `.ts` alone has no runtime effect, it must be
> compiled with `lrelease` and the resulting `.qm` committed.

## How to Add/Update Translations

### UI Translations (.ts files)

1. **File Structure**
   - Each translation file follows the Qt TS format
   - Files are named as `Seraphine.{locale}.ts` (e.g., `Seraphine.zh_CN.ts`)
   - Translations are organized by context (e.g., `ToolsTranslator`, `MainWindow`, `SettingInterface`)

2. **Adding New Translations**
   ```xml
   <context>
       <name>ContextName</name>
       <message>
           <location filename="../../path/to/source.py" line="123"/>
           <source>Original Text</source>
           <translation>Translated Text</translation>
       </message>
   </context>
   ```

3. **Compiling to `.qm`**
   ```shell
   lrelease app/resource/i18n/Seraphine.zh_CN.ts
   ```
   `main.py` loads translations by locale through `QTranslator`, so the compiled file must be named
   exactly `Seraphine.zh_CN.qm`.

4. **Best Practices**
   - Keep translations concise and natural
   - Maintain consistent terminology
   - Preserve any HTML tags in the original text
   - Test translations in the application

## Translation Guidelines

1. **General Rules**
   - Use proper grammar and punctuation
   - Maintain consistent terminology across all translations
   - Keep translations natural and idiomatic
   - Preserve any special characters or formatting

2. **Game-Specific Terms**
   - Use official League of Legends terminology
   - Keep champion names in English
   - Use consistent translations for roles and game modes
   - Follow Riot Games' style guide for game terms

3. **Technical Terms**
   - Keep technical terms in English if no common translation exists
   - Use consistent translations for UI elements
   - Maintain proper capitalization

## Testing Translations

1. **Before Submitting**
   - Test translations in the application
   - Verify all strings are properly translated
   - Check for any formatting issues
   - Ensure no translation keys are missing

2. **Common Issues to Check**
   - Missing translations
   - Incorrect formatting
   - Inconsistent terminology
   - Grammar and spelling errors

## Submitting Changes

1. **Pull Request Process**
   - Create a new branch for your translations
   - Update only the necessary translation files
   - Include a clear description of changes
   - Reference any related issues

2. **Commit Messages**
   - Use clear, descriptive commit messages
   - Specify which language(s) were updated
   - Mention the type of changes (new translations, updates, fixes)

## Getting Help

If you need assistance with translations:
- Open an issue on GitHub
- Join our community discussions
- Reference the official League of Legends terminology

## Code of Conduct

Please be respectful and professional when contributing translations. We aim to maintain a welcoming and inclusive community for all contributors.

## License

By contributing translations, you agree that your contributions will be licensed under the project's [GPLv3 license](LICENSE). 