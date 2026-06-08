import { Button, Card, Input, Label, TextField } from "@heroui/react";
import { useEffect, useState, type FormEvent } from "react";
import { api } from "../api";

export default function Profile() {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [age, setAge] = useState("");
  const [sex, setSex] = useState("");
  const [status, setStatus] = useState("");
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
    setStatus("");
    setError("");
    try {
      await api.updateProfile({
        full_name: fullName || null,
        age: age ? parseInt(age, 10) : null,
        sex: sex || null,
      });
      setStatus("Saved.");
    } catch (err) {
      setError((err as Error).message);
    }
}

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold">Profile</h1>
      <Card className="max-w-md">
        <Card.Header>
          <Card.Title>Your details</Card.Title>
          <Card.Description>{email}</Card.Description>
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
            <TextField fullWidth value={sex} onChange={setSex}>
              <Label>Sex</Label>
              <Input placeholder="e.g. female / male" />
            </TextField>
            <Button type="submit">Save</Button>
            {status && <p className="text-emerald-600">{status}</p>}
            {error && <p className="text-red-600">{error}</p>}
          </form>
        </Card.Content>
      </Card>
    </div>
  );
}
