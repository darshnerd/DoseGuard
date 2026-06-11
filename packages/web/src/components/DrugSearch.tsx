
import { InputGroup, Spinner, TextField } from "@heroui/react";
import { Search } from "lucide-react";
import { useEffect, useRef, useState } from "react";

export interface DrugHit {
  name: string;
  normalized: string;
  kind: string;
  manufacturer?: string | null;
}

interface Props {
  onSearch: (query: string) => Promise<DrugHit[]>;
  onSelect: (hit: DrugHit) => void;
  placeholder?: string;
}

export default function DrugSearch({ onSearch, onSelect, placeholder = "Search medicines or salts" }: Props) {
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<DrugHit[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  useEffect(() => {
    if (timer.current) clearTimeout(timer.current);
    const q = query.trim();
    if (q.length < 2) {
      setHits([]);
      setOpen(false);
      return;
    }
    let ignore = false;
    setLoading(true);
    timer.current = setTimeout(async () => {
      try {
        const results = await onSearch(q);
        if (ignore) return;
        setHits(results);
        setOpen(true);
      } finally {
        if (!ignore) setLoading(false);
      }
    }, 250);
    return () => {
      ignore = true;
      if (timer.current) clearTimeout(timer.current);
    };
}, [query, onSearch]);

  function pick(hit: DrugHit) {
    onSelect(hit);
    setQuery("");
    setHits([]);
    setOpen(false);
  }

  return (
    <div className="relative w-full">
      <TextField aria-label="Drug search" value={query} onChange={setQuery}>
        <InputGroup>
          <InputGroup.Prefix>
            <Search className="size-4 text-gray-400" />
          </InputGroup.Prefix>
          <InputGroup.Input placeholder={placeholder} />
          {loading && (
            <InputGroup.Suffix>
              <Spinner size="sm" />
            </InputGroup.Suffix>
          )}
        </InputGroup>
      </TextField>
      {open && hits.length > 0 && (
        <ul className="absolute z-20 mt-1 max-h-72 w-full overflow-auto rounded-xl border border-gray-100 bg-white shadow-lg">
          {hits.map((hit) => (
            <li key={`${hit.kind}:${hit.normalized}`}>
              <button
                type="button"
                onClick={() => pick(hit)}
                className="flex w-full flex-col items-start gap-0.5 px-4 py-2 text-left hover:bg-gray-50"
              >
                <span className="text-sm font-medium text-gray-900">{hit.name}</span>
                <span className="text-xs text-gray-400">
                  {hit.kind}
                  {hit.manufacturer ? ` · ${hit.manufacturer}` : ""}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
