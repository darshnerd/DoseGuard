import { Button, Card, Input } from "@heroui/react";
import { useEffect, useState, type FormEvent } from "react";
import { api, type Medication } from "../api";

export default function Medications() {
  const [meds, setMeds] = useState<Medication[]>([]);
  const [name, setName] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      setMeds(await api.listMedications());
    } catch (e) {
      setError((e as Error).message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function add(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    await api.addMedication(name.trim());
    setName("");
    load();
  }

  async function remove(id: number) {
    await api.deleteMedication(id);
    load();
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold">My medications</h1>
      <Card>
        <Card.Content>
          <form className="flex gap-2" onSubmit={add}>
            <Input
              fullWidth
              placeholder="Add a drug (e.g. warfarin)"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <Button type="submit">Add</Button>
          </form>
          <ul className="mt-4 flex flex-col gap-2">
            {meds.length === 0 && <li className="text-gray-500">No medications yet.</li>}
            {meds.map((m) => (
              <li
                key={m.id}
                className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2"
              >
                <span>
                  {m.name}
                  {m.ingredient && <em className="text-gray-500"> ({m.ingredient})</em>}
                </span>
                <Button isIconOnly size="sm" variant="danger" onPress={() => remove(m.id)}>
                  ✕
                </Button>
              </li>
            ))}
          </ul>
        </Card.Content>
      </Card>
      {error && <p className="text-red-600">{error}</p>}
    </div>
  );
}