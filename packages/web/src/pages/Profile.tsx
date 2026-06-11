import { Avatar, Button, Card, Chip, Input, Label, ListBox, Select, TextField } from "@heroui/react";
import { CheckCircle2, KeyRound, Mail, UserCircle } from "lucide-react";
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
  const [createdAt, setCreatedAt] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [pwSaved, setPwSaved] = useState(false);
  const [pwError, setPwError] = useState("");
  const [pwLoading, setPwLoading] = useState(false);

  useEffect(() => {
    api
      .getProfile()
      .then((p) => {
        setEmail(p.email);
        setFullName(p.full_name ?? "");
        setAge(p.age != null ? String(p.age) : "");
        setSex(p.sex ?? "");
        setCreatedAt(p.created_at);
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

  async function onChangePassword(e: FormEvent) {
    e.preventDefault();
    setPwSaved(false);
    setPwError("");
    if (newPw.length < 8) return setPwError("New password must be at least 8 characters.");
    if (newPw !== confirmPw) return setPwError("New passwords do not match.");
    setPwLoading(true);
    try {
      await api.changePassword(currentPw, newPw);
      setPwSaved(true);
      setCurrentPw("");
      setNewPw("");
      setConfirmPw("");
      window.setTimeout(() => setPwSaved(false), 2000);
    } catch (err) {
      setPwError((err as Error).message);
    } finally {
      setPwLoading(false);
    }
  }

  const initials = (fullName || email || "?").slice(0, 2).toUpperCase();
  const sexLabel = SEX_OPTIONS.find((o) => o.id === sex)?.label;
  const memberSince = createdAt
    ? new Date(createdAt).toLocaleDateString(undefined, { year: "numeric", month: "long" })
    : null;

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6">
      <PageHeader icon={UserCircle} title="Profile" subtitle="Manage your account details." />

      <div className="grid gap-6 lg:grid-cols-3">
        <FadeItem className="lg:col-span-1">
          <Card className="h-full">
            <Card.Content className="h-full">
              <div className="flex h-full flex-col items-center justify-center gap-3 py-2 text-center">
                <Avatar size="lg">
                  <Avatar.Fallback>{initials}</Avatar.Fallback>
                </Avatar>
                <div>
                  <div className="font-semibold text-gray-900">{fullName || "Your profile"}</div>
                  <div className="flex items-center justify-center gap-1 text-sm text-gray-500">
                    <Mail className="size-3.5" /> {email}
                  </div>
                </div>
                {(age || sexLabel) && (
                  <div className="flex flex-wrap justify-center gap-2">
                    {age && <Chip size="sm" variant="soft">Age {age}</Chip>}
                    {sexLabel && <Chip size="sm" variant="soft">{sexLabel}</Chip>}
                  </div>
                )}
                {memberSince && <p className="text-xs text-gray-400">Member since {memberSince}</p>}
              </div>
            </Card.Content>
          </Card>
        </FadeItem>

        <FadeItem className="lg:col-span-2">
          <Card className={saved ? "animate-success-flash" : ""}>
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

                <div className="grid gap-4 sm:grid-cols-2">
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
                </div>

                <div className="flex items-center gap-3">
                  <Button type="submit">Save</Button>
                  {saved && (
                    <p className="flex items-center gap-1 text-emerald-600">
                      <CheckCircle2 className="size-4" /> Saved.
                    </p>
                  )}
                </div>
                {error && <p className="text-red-600">{error}</p>}
              </form>
            </Card.Content>
          </Card>
        </FadeItem>
      </div>

      <FadeItem>
        <Card className={pwSaved ? "animate-success-flash" : ""}>
          <Card.Header>
            <Card.Title className="flex items-center gap-2">
              <KeyRound className="size-4 text-gray-500" /> Change password
            </Card.Title>
            <Card.Description>Other devices will be signed out.</Card.Description>
          </Card.Header>
          <Card.Content>
            <form className="flex flex-col gap-4" onSubmit={onChangePassword}>
              <TextField fullWidth type="password" value={currentPw} onChange={setCurrentPw}>
                <Label>Current password</Label>
                <Input placeholder="••••••••" />
              </TextField>
              <div className="grid gap-4 sm:grid-cols-2">
                <TextField fullWidth type="password" value={newPw} onChange={setNewPw}>
                  <Label>New password</Label>
                  <Input placeholder="At least 8 characters" />
                </TextField>
                <TextField fullWidth type="password" value={confirmPw} onChange={setConfirmPw}>
                  <Label>Confirm new password</Label>
                  <Input placeholder="Re-enter new password" />
                </TextField>
              </div>
              <div className="flex items-center gap-3">
                <Button
                  type="submit"
                  isPending={pwLoading}
                  isDisabled={pwLoading || !currentPw || !newPw || !confirmPw}
                >
                  {pwLoading ? "Updating…" : "Update password"}
                </Button>
                {pwSaved && (
                  <p className="flex items-center gap-1 text-emerald-600">
                    <CheckCircle2 className="size-4" /> Password updated.
                  </p>
                )}
              </div>
              {pwError && <p className="text-red-600">{pwError}</p>}
            </form>
          </Card.Content>
        </Card>
      </FadeItem>
    </div>
  );
}
