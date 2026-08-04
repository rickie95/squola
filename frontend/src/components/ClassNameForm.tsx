import type { SchoolClassCreate } from "../types";

const ROMAN_NUMERALS = ["I", "II", "III", "IV", "V"];
const SECTIONS = ["A", "B", "C", "D", "E", "F"];

interface ClassNameFormProps {
  value: SchoolClassCreate;
  onChange: (data: SchoolClassCreate) => void;
}

export default function ClassNameForm({ value, onChange }: ClassNameFormProps) {
  return (
    <div className="form-row">
      <div className="form-group">
        <label htmlFor="year">Anno</label>
        <select
          id="year"
          value={value.year}
          onChange={(e) => onChange({ ...value, year: e.target.value })}
        >
          {ROMAN_NUMERALS.map((numeral) => (
            <option key={numeral} value={numeral}>
              {numeral}
            </option>
          ))}
        </select>
      </div>
      <div className="form-group">
        <label htmlFor="section">Sezione</label>
        <select
          id="section"
          value={value.section}
          onChange={(e) => onChange({ ...value, section: e.target.value })}
        >
          {SECTIONS.map((section) => (
            <option key={section} value={section}>
              {section}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
