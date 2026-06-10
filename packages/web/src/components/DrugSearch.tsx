
import { Input, Spinner } from "@heroui/react";
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
  const timer = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    if (timer.current) clearTimeout(timer.current);
    const q = query.trim();
    if (q.length < 2) {
      setHits([]);
      setOpen(false);
      return;
    }
    setLoading(true);
    timer.current = setTimeout(async () => {
      try {
        const results = await onSearch(q);
        setHits(results);
        setOpen(true);
      } finally {
        setLoading(false);
      }
    }, 250);
    return () => {
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
      <Input
        value={query}
        onValueChange={setQuery}
        placeholder={placeholder}
        startContent={<Search className="size-4 text-gray-400" />}
        endContent={loading ? <Spinner size="sm" /> : null}
      />
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
