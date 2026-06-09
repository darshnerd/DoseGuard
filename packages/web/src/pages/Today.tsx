import { Alert, Button, Card, Chip, ProgressCircle, Spinner, Tooltip } from "@heroui/react";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  CalendarDays,
  Check,
  Circle,
  Clock,
  Moon,
  Sun,
  Sunrise,
  Sunset,
  X,
  type LucideIcon,
} from "lucide-react";
import { useEffect, useState } from "react";
import { api, type Adherence, type DoseStatus, type Slot, type TodayResponse } from "../api";
import { FadeItem, PageHeader, Stagger } from "../components/ui";

const SLOT_META: Record<Slot, { label: string; icon: LucideIcon; tint: string }> = {
  morning: { label: "Morning", icon: Sunrise, tint: "from-amber-50 to-orange-50/40" },
  afternoon: { label: "Afternoon", icon: Sun, tint: "from-sky-50 to-blue-50/40" },
  evening: { label: "Evening", icon: Sunset, tint: "from-indigo-50 to-violet-50/40" },
  night: { label: "Night", icon: Moon, tint: "from-slate-100 to-slate-50" },
};

const STATUS_META: Record<
  DoseStatus,
  { label: string; color: "success" | "danger" | "warning" | "default"; icon: LucideIcon }
> = {
  taken: { label: "Taken", color: "success", icon: Check },
  overdue: { label: "Overdue", color: "danger", icon: Clock },
  upcoming: { label: "Upcoming", color: "default", icon: Circle },
  skipped: { label: "Skipped", color: "warning", icon: X },
};

function ringColor(p: number): "success" | "warning" | "danger" {
  return p >= 80 ? "success" : p >= 50 ? "warning" : "danger";
}

function AdherenceRing({ percent, adherence }: { percent: number; adherence: Adherence | null }) {
  const hasSchedule = (adherence?.expected ?? 0) > 0;
  return (
    <Card>
      <Card.Content>
        <div className="flex items-center gap-5">
          <div className="relative inline-flex size-28 items-center justify-center">
            <ProgressCircle
              aria-label="7-day adherence"
              value={percent}
              color={ringColor(percent)}
              size="lg"
              className="size-28"
            >
              <ProgressCircle.Track>
                <ProgressCircle.TrackCircle />
                <ProgressCircle.FillCircle />
              </ProgressCircle.Track>
            </ProgressCircle>
            <span className="absolute text-2xl font-bold text-gray-900">
              {hasSchedule ? `${percent}%` : "—"}
            </span>
          </div>
          <div>
            <div className="text-sm font-medium text-gray-500">7-day adherence</div>
            {hasSchedule ? (
              <>
                <div className="mt-1 text-lg font-semibold text-gray-900">
                  {percent >= 80 ? "On track 🎯" : percent >= 50 ? "Keep going 💪" : "Needs attention"}
                </div>
                <div className="mt-1 text-sm text-gray-500">
                  {adherence!.taken} of {adherence!.expected} doses taken
                </div>
              </>
            ) : (
              <>
                <div className="mt-1 text-lg font-semibold text-gray-900">No schedule yet</div>
                <div className="mt-1 text-sm text-gray-500">
                  Assign slots to your meds to start tracking.
                </div>
              </>
            )}
          </div>
        </div>
      </Card.Content>
    </Card>
  );
}

function StatusBar({ counts, total }: { counts: Record<DoseStatus, number>; total: number }) {
  if (total === 0) return null;
  const segs: { status: DoseStatus; cls: string }[] = [
    { status: "taken", cls: "bg-emerald-500" },
    { status: "upcoming", cls: "bg-gray-300" },
    { status: "overdue", cls: "bg-red-500" },
    { status: "skipped", cls: "bg-amber-400" },
  ];
  return (
    <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-gray-100">
      {segs.map(
        (s) =>
          counts[s.status] > 0 && (
            <motion.div
              key={s.status}
              className={s.cls}
              initial={{ width: 0 }}
              animate={{ width: `${(counts[s.status] / total) * 100}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
            />
          )
      )}
    </div>
  );
}

export default function Today() {
  const [data, setData] = useState<TodayResponse | null>(null);
  const [adherence, setAdherence] = useState<Adherence | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [flashed, setFlashed] = useState<Set<string>>(new Set());

  async function load() {
    try {
      const [today, adh] = await Promise.all([api.getToday(), api.getAdherence()]);
      setData(today);
      setAdherence(adh);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function act(medId: number, slot: Slot, status: "taken" | "skipped") {
    const key = `${medId}-${slot}`;
    setBusy(key);
    try {
      await api.logDose(medId, slot, status);
      await load();
      setFlashed((prev) => new Set(prev).add(key));
      window.setTimeout(
        () =>
          setFlashed((prev) => {
            const next = new Set(prev);
            next.delete(key);
            return next;
          }),
        700
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(null);
    }
  }

  if (!data) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner color="accent" size="lg" />
      </div>
    );
  }

  const allItems = data.slots.flatMap((s) => s.items);
  const counts: Record<DoseStatus, number> = { taken: 0, skipped: 0, overdue: 0, upcoming: 0 };
  for (const it of allItems) counts[it.status] += 1;
  const total = allItems.length;
  const remaining = counts.upcoming + counts.overdue;

  const overdue = data.slots.flatMap((s) =>
    s.items.filter((i) => i.status === "overdue").map((i) => ({ ...i, slot: s.slot }))
  );

  return (
    <div className="flex flex-col gap-6">
      <PageHeader icon={CalendarDays} title="My day" subtitle={data.date} />

      {/* Summary strip */}
      <Stagger className="grid grid-cols-1 gap-4 lg:grid-cols-[1.4fr_1fr]">
        <FadeItem>
          <AdherenceRing percent={data.adherence} adherence={adherence} />
        </FadeItem>
        <FadeItem>
          <Card>
            <Card.Content>
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium text-gray-500">Today</div>
                <Chip color={remaining === 0 && total > 0 ? "success" : "default"}>
                  {remaining === 0 && total > 0 ? "All caught up ✓" : `${remaining} left`}
                </Chip>
              </div>
              <div className="mt-3 flex gap-4 text-center">
                <div className="flex-1">
                  <div className="text-2xl font-bold text-emerald-600">{counts.taken}</div>
                  <div className="text-xs text-gray-500">Taken</div>
                </div>
                <div className="flex-1">
                  <div className="text-2xl font-bold text-red-600">{counts.overdue}</div>
                  <div className="text-xs text-gray-500">Overdue</div>
                </div>
                <div className="flex-1">
                  <div className="text-2xl font-bold text-gray-700">{counts.upcoming}</div>
                  <div className="text-xs text-gray-500">Upcoming</div>
                </div>
              </div>
              <div className="mt-4">
                <StatusBar counts={counts} total={total} />
              </div>
            </Card.Content>
          </Card>
        </FadeItem>
      </Stagger>

      {/* Overdue catch-up */}
      {overdue.length > 0 && (
        <FadeItem>
          <Alert status="warning">
            <Alert.Indicator />
            <Alert.Content>
              <Alert.Title>
                {overdue.length} dose{overdue.length > 1 ? "s" : ""} overdue
              </Alert.Title>
              <Alert.Description>
                {overdue.map((o) => `${o.name} (${SLOT_META[o.slot].label})`).join(", ")}
              </Alert.Description>
            </Alert.Content>
          </Alert>
        </FadeItem>
      )}

      {/* Slot cards */}
      <Stagger className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {data.slots.map((slot) => {
          const meta = SLOT_META[slot.slot];
          const SlotIcon = meta.icon;
          const taken = slot.items.filter((i) => i.status === "taken").length;
          return (
            <FadeItem key={slot.slot}>
              <Card className={`bg-gradient-to-br ${meta.tint}`}>
                <Card.Header>
                  <Card.Title className="flex items-center gap-2">
                    <SlotIcon className="size-5 text-gray-600" /> {meta.label}
                  </Card.Title>
                  {slot.items.length > 0 && (
                    <Chip size="sm" color={taken === slot.items.length ? "success" : "default"}>
                      {taken}/{slot.items.length}
                    </Chip>
                  )}
                </Card.Header>
                <Card.Content>
                  {slot.warnings.length > 0 && (
                    <Tooltip>
                      <Tooltip.Trigger>
                        <div className="mb-3 inline-flex">
                          <Chip color="warning" variant="soft">
                            <AlertTriangle className="size-3" /> Interaction in this slot
                          </Chip>
                        </div>
                      </Tooltip.Trigger>
                      <Tooltip.Content showArrow>{slot.warnings.join(" · ")}</Tooltip.Content>
                    </Tooltip>
                  )}

                  {slot.items.length === 0 ? (
                    <p className="py-2 text-sm text-gray-400">Nothing scheduled.</p>
                  ) : (
                    <ul className="flex flex-col gap-2">
                      {slot.items.map((item) => {
                        const s = STATUS_META[item.status];
                        const StatusIcon = s.icon;
                        const key = `${item.medication_id}-${slot.slot}`;
                        const isBusy = busy === key;
                        const isFlashed = flashed.has(key);
                        return (
                          <li
                            key={item.medication_id}
                            className={`flex items-center justify-between gap-2 rounded-xl bg-white/70 px-3 py-2 backdrop-blur transition-all ${
                              isFlashed ? "animate-success-flash" : ""
                            }`}
                          >
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{item.name}</span>
                              <Chip color={s.color} size="sm">
                                <StatusIcon className="size-3" /> {s.label}
                              </Chip>
                            </div>
                            <div className="flex gap-1.5">
                              <Button
                                size="sm"
                                isDisabled={isBusy || item.status === "taken"}
                                onPress={() => act(item.medication_id, slot.slot, "taken")}
                              >
                                <Check className="mr-1 size-4" /> Take
                              </Button>
                              <Button
                                size="sm"
                                variant="tertiary"
                                isDisabled={isBusy || item.status === "skipped"}
                                onPress={() => act(item.medication_id, slot.slot, "skipped")}
                              >
                                Skip
                              </Button>
                            </div>
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </Card.Content>
              </Card>
            </FadeItem>
          );
        })}
      </Stagger>

      {error && <p className="text-red-600">{error}</p>}
    </div>
  );
}
