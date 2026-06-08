import { Alert, Button, Card, Input, Label, TextField } from "@heroui/react";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <Card className="w-full max-w-sm">
        <Card.Header>
          <Card.Title>🛡️ DoseGuard</Card.Title>
          <Card.Description>Log in to check your medications.</Card.Description>
        </Card.Header>
        <Card.Content>
          <form className="flex flex-col gap-4" onSubmit={onSubmit}>
            <TextField fullWidth name="email" type="email" value={email} onChange={setEmail}>
              <Label>Email</Label>
              <Input placeholder="you@example.com" />
            </TextField>
            <TextField fullWidth name="password" type="password" value={password} onChange={setPassword}>
              <Label>Password</Label>
              <Input placeholder="••••••••" />
            </TextField>
            {error && (
              <Alert status="danger">
                <Alert.Indicator />
                <Alert.Content>
                  <Alert.Title>{error}</Alert.Title>
                </Alert.Content>
              </Alert>
            )}
            <Button fullWidth type="submit">Log in</Button>
          </form>
        </Card.Content>
        <Card.Footer>
          <span className="text-sm text-gray-600">No account? <Link className="text-blue-600" to="/register">Register</Link></span>
        </Card.Footer>
      </Card>
    </div>
  );
}
