import { Calendar as HeroCalendar, Card, Spinner } from "@heroui/react";
import { CalendarCheck, CheckCheck, TrendingUp } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api, type DayStat } from "../api";
import { FadeItem, PageHeader, Stat } from "../components/ui";

const todayIso = new Date().toISOString().slice(0, 10);

type DayState = "complete" | "partial" | "missed" | "pending" | "none";

function dayState(d: DayStat): DayState {
  if (d.expected === 0) return "none";
  if (d.taken >= d.expected) return "complete";
  if (d.taken > 0) return "partial";
  return d.date >= todayIso ? "pending" : "missed";
}

const DOT: Record<DayState, string> = {
  complete: "bg-emerald-500",
  partial: "bg-amber-400",
  missed: "bg-red-500",
  pending: "bg-blue-400",
  none: "",
};

const LEGEND = [
  { cls: "bg-emerald-500", label: "All taken" },
  { cls: "bg-amber-400", label: "Partial" },
  { cls: "bg-red-500", label: "Missed" },
  { cls: "bg-blue-400", label: "Today / pending" },
];

export default function CalendarPage() {
  const [history, setHistory] = useState<DayStat[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getHistory(90).then(setHistory).catch((e) => setError((e as Error).message));
  }, []);

  const byDate = useMemo(() => {
    const m: Record<string, DayStat> = {};
    for (const d of history ?? []) m[d.date] = d;
    return m;
  }, [history]);

  const stats = useMemo(() => {
    const days = history ?? [];
    const totalTaken = days.reduce((s, d) => s + d.taken, 0);
    const trackedDays = days.filter((d) => d.expected > 0).length;

    // Last 12 weeks of adherence (oldest→newest chunks of 7).
    const weeks: { pct: number | null }[] = [];
    for (let i = Math.max(0, days.length - 84); i < days.length; i += 7) {
      const chunk = days.slice(i, i + 7);
      const e = chunk.reduce((s, d) => s + d.expected, 0);
      const t = chunk.reduce((s, d) => s + d.taken, 0);
      weeks.push({ pct: e ? Math.round((t / e) * 100) : null });
    }

    return { totalTaken, trackedDays, weeks };
  }, [history]);

  if (!history) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner color="accent" size="lg" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader icon={CalendarCheck} title="Calendar" subtitle="Your dose history, day by day." />

      {/* Calendar (full width) */}
      <FadeItem>
        <Card>
          <Card.Content>
            <div className="mx-auto flex max-w-2xl flex-col items-center gap-4">
              <HeroCalendar aria-label="Dose history" isReadOnly className="w-full text-base">
                <HeroCalendar.Header>
                  <HeroCalendar.NavButton slot="previous" />
                  <HeroCalendar.Heading />
                  <HeroCalendar.NavButton slot="next" />
                </HeroCalendar.Header>
                <HeroCalendar.Grid className="w-full">
                  <HeroCalendar.GridHeader>
                    {(day) => (
                      <HeroCalendar.HeaderCell className="pb-2 text-sm font-medium text-gray-500">
                        {day}
                      </HeroCalendar.HeaderCell>
                    )}
                  </HeroCalendar.GridHeader>
                  <HeroCalendar.GridBody>
                    {(date) => {
                      const info = byDate[date.toString()];
                      const state = info ? dayState(info) : "none";
                      return (
                        <HeroCalendar.Cell date={date} className="p-1">
                          {({ formattedDate }) => (
                            <span className="relative flex size-11 items-center justify-center rounded-xl text-sm transition-colors hover:bg-gray-100 md:size-14 md:text-base">
                              {formattedDate}
                              {state !== "none" && (
                                <span
                                  className={`absolute bottom-1.5 size-1.5 rounded-full ${DOT[state]} md:size-2`}
                                />
                              )}
                            </span>
                          )}
                        </HeroCalendar.Cell>
                      );
                    }}
                  </HeroCalendar.GridBody>
                </HeroCalendar.Grid>
              </HeroCalendar>

              <div className="flex flex-wrap justify-center gap-4">
                {LEGEND.map((l) => (
                  <span key={l.label} className="flex items-center gap-1.5 text-sm text-gray-600">
                    <span className={`size-2.5 rounded-full ${l.cls}`} /> {l.label}
                  </span>
                ))}
              </div>
            </div>
          </Card.Content>
        </Card>
      </FadeItem>

      {/* Bottom: doses taken, tracked days, weekly adherence */}
      <div className="grid grid-cols-2 gap-4">
        <Stat icon={CheckCheck} label="Doses taken (90d)" value={stats.totalTaken} />
        <Stat icon={CalendarCheck} label="Tracked days" value={stats.trackedDays} />
      </div>

      <FadeItem>
        <Card>
          <Card.Header>
            <Card.Title className="flex items-center gap-2">
              <TrendingUp className="size-4 text-gray-500" /> Weekly adherence
            </Card.Title>
            <Card.Description>Last 12 weeks.</Card.Description>
          </Card.Header>
          <Card.Content>
            {stats.weeks.every((w) => w.pct === null) ? (
              <p className="text-sm text-gray-400">No scheduled doses yet.</p>
            ) : (
              <div className="flex h-32 items-end gap-1.5">
                {stats.weeks.map((w, i) => (
                  <div key={i} className="flex flex-1 flex-col items-center gap-1">
                    <div className="flex h-28 w-full items-end rounded bg-gray-100">
                      <div
                        className={`w-full rounded transition-all duration-500 ${
                          w.pct == null
                            ? ""
                            : w.pct >= 80
                              ? "bg-emerald-500"
                              : w.pct >= 50
                                ? "bg-amber-400"
                                : "bg-red-500"
                        }`}
                        style={{ height: `${w.pct ?? 0}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-gray-400">{w.pct == null ? "—" : w.pct}</span>
                  </div>
                ))}
              </div>
            )}
          </Card.Content>
        </Card>
      </FadeItem>

      {error && <p className="text-red-600">{error}</p>}
    </div>
  );
}
