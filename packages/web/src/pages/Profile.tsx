import { Button, Card, Input, Label, ListBox, Select, TextField } from "@heroui/react";
import { CheckCircle2, UserCircle } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { api } from "../api";
import { FadeItem, PageHeader } from "../components/ui";

const SEX_OPTIONS = [
  { id: "female", label: "Female" },
  { id: "male", label: "Male" },
  { id: "other", label: "Other" },
  { id: "prefer_not", label: "Prefer not to say" },
];

export default function Profile() {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [age, setAge] = useState("");
  const [sex, setSex] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getProfile()
      .then((p) => {
        setEmail(p.email);
        setFullName(p.full_name ?? "");
        setAge(p.age != null ? String(p.age) : "");
        setSex(p.sex ?? "");
      })
      .catch((e) => setError((e as Error).message));
    }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSaved(false);
    setError("");
    try {
      await api.updateProfile({
        full_name: fullName || null,
        age: age ? parseInt(age, 10) : null,
        sex: sex || null,
      });
      setSaved(true);
      window.setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader icon={UserCircle} title="Profile" subtitle={email} />
      <FadeItem>
        <Card className={`max-w-md ${saved ? "animate-success-flash" : ""}`}>
          <Card.Header>
            <Card.Title>Your details</Card.Title>
            <Card.Description>Used to personalize safety checks.</Card.Description>
          </Card.Header>
          <Card.Content>
            <form className="flex flex-col gap-4" onSubmit={onSubmit}>
              <TextField fullWidth value={fullName} onChange={setFullName}>
                <Label>Full name</Label>
                <Input placeholder="Jane Doe" />
              </TextField>
              <TextField fullWidth value={age} onChange={setAge}>
                <Label>Age</Label>
                <Input type="number" min={0} placeholder="30" />
              </TextField>

              <Select
                placeholder="Select"
                selectedKey={sex || null}
                onSelectionChange={(key) => setSex(key ? String(key) : "")}
              >
                <Label>Sex</Label>
                <Select.Trigger>
                  <Select.Value />
                  <Select.Indicator />
                </Select.Trigger>
                <Select.Popover>
                  <ListBox>
                    {SEX_OPTIONS.map((o) => (
                      <ListBox.Item key={o.id} id={o.id} textValue={o.label}>
                        {o.label}
                        <ListBox.ItemIndicator />
                      </ListBox.Item>
                    ))}
                  </ListBox>
                </Select.Popover>
              </Select>

              <Button type="submit">Save</Button>
              {saved && (
                <p className="flex items-center gap-1 text-emerald-600">
                  <CheckCircle2 className="size-4" /> Saved.
                </p>
              )}
              {error && <p className="text-red-600">{error}</p>}
            </form>
          </Card.Content>
        </Card>
      </FadeItem>
    </div>
  );
}
