"use client";

import { LanguageCode } from "@/lib/api";
import { LANGUAGES } from "@/lib/i18n/languages";

export function LanguageSelector(props: { value: LanguageCode; onChange: (code: LanguageCode) => void }) {
  return (
    <div className="field">
      <label htmlFor="voice-language">Language</label>
      <select
        id="voice-language"
        value={props.value}
        onChange={(event) => props.onChange(event.target.value as LanguageCode)}
      >
        {LANGUAGES.map((language) => (
          <option key={language.code} value={language.code}>
            {language.label}
          </option>
        ))}
      </select>
    </div>
  );
}
