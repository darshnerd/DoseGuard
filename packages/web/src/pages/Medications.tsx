import { Button, Card, Chip, Input, Modal, ToggleButton } from "@heroui/react";
import {
  Moon,
  Pill,
  Plus,
  ScanLine,
  Sun,
  Sunrise,
  Sunset,
  Trash2,
  type LucideIcon,
} from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api, type Medication, type ScanRecord, type Slot } from "../api";
import { FadeItem, PageHeader, Stagger } from "../components/ui";
import DrugSearch from "../components/DrugSearch";

const SLOTS: { slot: Slot; label: string; icon: LucideIcon }[] = [
  { slot: "morning", label: "Morning", icon: Sunrise },
  { slot: "afternoon", label: "Afternoon", icon: Sun },
  { slot: "evening", label: "Evening", icon: Sunset },
  { slot: "night", label: "Night", icon: Moon },
];

function DurationControl({
  value,
  onChange,
}: {
  value: number | null;
  onChange: (v: number) => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <Input
        type="number"
        min={1}
        className="w-28"
        placeholder="Days"
        value={value == null ? "" : String(value)}
        onChange={(e) => {
          const n = parseInt(e.target.value, 10);
          if (Number.isFinite(n) && n > 0) onChange(n);
        }}
      />
      <span className="text-sm text-gray-500">days</span>
    </div>
  );
}

function CourseEditor({
  med,
  onSave,
}: {
  med: Medication;
  onSave: (med: Medication, days: number) => Promise<void>;
}) {
  const [val, setVal] = useState(med.duration_days != null ? String(med.duration_days) : "");
  const [saving, setSaving] = useState(false);
  const n = parseInt(val, 10);
  const valid = Number.isFinite(n) && n > 0;
  const changed = valid && n !== med.duration_days;

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-sm text-gray-500">Course</span>
      <Input
        type="number"
        min={1}
        className="w-24"
        placeholder="Days"
        value={val}
        onChange={(e) => setVal(e.target.value)}
      />
      <span className="text-sm text-gray-500">days</span>
      <Button
        size="sm"
        variant="secondary"
        isDisabled={!changed || saving}
        isPending={saving}
        onPress={async () => {
          setSaving(true);
          try {
            await onSave(med, n);
          } finally {
            setSaving(false);
          }
        }}
      >
        Save
      </Button>
    </div>
  );
}

function courseChip(m: Medication): { text: string; color: "default" | "accent" | "success" } {
  if (m.duration_days == null) return { text: "Ongoing", color: "default" };
  const start = new Date(`${m.start_date}T00:00:00`);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const dayNo = Math.floor((today.getTime() - start.getTime()) / 86_400_000) + 1;
  if (dayNo < 1) return { text: `Starts in ${1 - dayNo}d`, color: "accent" };
  if (dayNo > m.duration_days) return { text: "Completed", color: "success" };
  return { text: `Day ${dayNo} of ${m.duration_days}`, color: "accent" };
}

function AddFromScanModal({
  scans,
  onAdd,
}: {
  scans: ScanRecord[];
  onAdd: (name: string, drugs: string[], durationDays: number) => Promise<boolean>;
}) {
  const usable = scans.filter((s) => s.drugs.length > 0);
  const [names, setNames] = useState<Record<number, string>>({});
  const [durations, setDurations] = useState<Record<number, number | null>>({});
  const [adding, setAdding] = useState<number | null>(null);

  useEffect(() => {
    setNames((prev) => {
      const next = { ...prev };
      for (const s of usable) if (!(s.id in next)) next[s.id] = s.drugs.join(" + ");
      return next;
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scans]);

  async function add(scan: ScanRecord) {
    const name = (names[scan.id] ?? scan.drugs.join(" + ")).trim();
    const d = durations[scan.id];
    if (!name || !d || d < 1) return;
    setAdding(scan.id);
    try {
      await onAdd(name, scan.drugs, d);
    } finally {
      setAdding(null);
    }
  }

  return (
    <Modal>
      <Button variant="secondary">
        <ScanLine className="mr-1 size-4" /> Add from scan
      </Button>
      <Modal.Backdrop>
        <Modal.Container>
          <Modal.Dialog className="sm:max-w-[600px]">
            <Modal.CloseTrigger />
            <Modal.Header>
              <Modal.Heading>Add a medication from a scan</Modal.Heading>
            </Modal.Header>
            <Modal.Body>
              {usable.length === 0 ? (
                <p className="text-gray-500">
                  No scans with detected drugs yet.{" "}
                  <Link to="/scan" className="font-medium text-brand hover:underline">
                    Scan a label
                  </Link>{" "}
                  first.
                </p>
              ) : (
                <div className="flex flex-col gap-4">
                  <p className="text-sm text-gray-500">
                    Each scan is added as one medication. Set how long it's prescribed for.
                  </p>
                  {usable.map((scan) => (
                    <div key={scan.id} className="rounded-xl border border-gray-200 p-3">
                      <div className="mb-2 flex flex-wrap items-center gap-2">
                        <span className="text-xs text-gray-400">
                          {new Date(scan.created_at).toLocaleDateString()}
                        </span>
                        {scan.drugs.map((d) => (
                          <Chip key={d} size="sm" variant="soft">
                            {d}
                          </Chip>
                        ))}
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <Input
                          className="min-w-[180px] flex-1"
                          placeholder="Name this medication"
                          value={names[scan.id] ?? ""}
                          onChange={(e) =>
                            setNames((prev) => ({ ...prev, [scan.id]: e.target.value }))
                          }
                        />
                        <DurationControl
                          value={durations[scan.id] ?? null}
                          onChange={(v) => setDurations((prev) => ({ ...prev, [scan.id]: v }))}
                        />
                        <Button
                          size="sm"
                          isPending={adding === scan.id}
                          isDisabled={adding !== null || !durations[scan.id]}
                          onPress={() => add(scan)}
                        >
                          <Plus className="mr-1 size-4" /> Add
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Modal.Body>
            <Modal.Footer>
              <Button slot="close" variant="tertiary">
                Done
              </Button>
            </Modal.Footer>
          </Modal.Dialog>
        </Modal.Container>
      </Modal.Backdrop>
    </Modal>
  );
}

export default function Medications() {
  const [meds, setMeds] = useState<Medication[]>([]);
  const [scans, setScans] = useState<ScanRecord[]>([]);
  const [schedules, setSchedules] = useState<Record<number, Slot[]>>({});
  const [name, setName] = useState("");
  const [days, setDays] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      const [medList, scheduleList, scanList] = await Promise.all([
        api.listMedications(),
        api.getSchedule(),
        api.listScans(),
      ]);
      setMeds(medList);
      setScans(scanList);
      const map: Record<number, Slot[]> = {};
      for (const s of scheduleList) map[s.medication_id] = s.slots;
      setSchedules(map);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function addByName(
    value: string,
    drugs: string[] | undefined,
    durationDays: number
  ): Promise<boolean> {
    if (!value.trim()) return false;
    setError("");
    try {
      await api.addMedication(value.trim(), drugs, durationDays);
      await load();
      return true;
    } catch (e) {
      setError((e as Error).message);
      return false;
    }
  }

  function parsedDays(): number | null {
    const n = parseInt(days, 10);
    return Number.isFinite(n) && n > 0 ? n : null;
  }

  function pick(value: string) {
    const n = parsedDays();
    if (!n) {
      setError("Enter the number of days before adding.");
      return;
    }
    addByName(value, undefined, n);
  }

  async function add(e: FormEvent) {
    e.preventDefault();
    const n = parsedDays();
    if (!name.trim() || !n) {
      setError("Enter a medicine name and number of days.");
      return;
    }
    if (await addByName(name, undefined, n)) setName("");
  }

  async function setDuration(med: Medication, duration: number) {
    setMeds((prev) => prev.map((m) => (m.id === med.id ? { ...m, duration_days: duration } : m)));
    try {
      await api.updateMedication(med.id, { duration_days: duration });
    } catch (e) {
      setError((e as Error).message);
      load();
    }
  }

  async function remove(id: number) {
    await api.deleteMedication(id);
    load();
  }

  async function toggleSlot(medId: number, slot: Slot) {
    const current = schedules[medId] ?? [];
    const next = current.includes(slot)
      ? current.filter((s) => s !== slot)
      : [...current, slot];
    setSchedules({ ...schedules, [medId]: next });
    try {
      await api.setSchedule(medId, next);
    } catch (e) {
      setError((e as Error).message);
      load();
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader icon={Pill} title="My medications" subtitle="Add meds, set the course, assign slots." />

      <FadeItem>
        <Card>
          <Card.Content>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
              <div className="flex-1">
                <DrugSearch
                  onSearch={api.searchDrugs}
                  onSelect={(hit) => pick(hit.name)}
                  placeholder="Search a medicine or salt (e.g. warfarin)"
                />
              </div>
              <form className="flex gap-2" onSubmit={add}>
                <Input
                  placeholder="…or type a name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
                <Input
                  type="number"
                  min={1}
                  className="w-24"
                  placeholder="Days"
                  value={days}
                  onChange={(e) => setDays(e.target.value)}
                />
                <Button type="submit">
                  <Plus className="mr-1 size-4" /> Add
                </Button>
                <AddFromScanModal scans={scans} onAdd={addByName} />
              </form>
            </div>
          </Card.Content>
        </Card>
      </FadeItem>

      {meds.length === 0 ? (
        <p className="text-gray-500">No medications yet.</p>
      ) : (
        <Stagger className="flex flex-col gap-3">
          {meds.map((m) => {
            const active = schedules[m.id] ?? [];
            const course = courseChip(m);
            return (
              <FadeItem key={m.id}>
                <Card className="transition-shadow hover:shadow-md">
                  <Card.Content>
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2 font-medium">
                          {m.name}
                          <Chip size="sm" color={course.color}>
                            {course.text}
                          </Chip>
                        </div>
                        {m.ingredients.length > 0 && (
                          <div className="mt-1 flex flex-wrap gap-1">
                            {m.ingredients.map((ing) => (
                              <Chip key={ing.ingredient} size="sm" variant="soft">
                                {ing.ingredient}
                              </Chip>
                            ))}
                          </div>
                        )}
                      </div>
                      <Button isIconOnly size="sm" variant="danger" onPress={() => remove(m.id)}>
                        <Trash2 className="size-4" />
                      </Button>
                    </div>

                    <div className="mt-3">
                      <CourseEditor med={m} onSave={setDuration} />
                    </div>

                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {SLOTS.map(({ slot, label, icon: Icon }) => (
                        <ToggleButton
                          key={slot}
                          size="sm"
                          isSelected={active.includes(slot)}
                          onChange={() => toggleSlot(m.id, slot)}
                        >
                          <Icon className="mr-1 size-4" />
                          {label}
                        </ToggleButton>
                      ))}
                    </div>
                  </Card.Content>
                </Card>
              </FadeItem>
            );
          })}
        </Stagger>
      )}

      {error && <p className="text-red-600">{error}</p>}
    </div>
  );
}