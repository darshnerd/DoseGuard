import { Alert, Button, Card, Input, Label, TextField } from "@heroui/react";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

export default function Register() {
  const { register, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await register(email, password);
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
          <Card.Title>Create your account</Card.Title>
          <Card.Description>Start tracking your medications safely.</Card.Description>
        </Card.Header>
        <Card.Content>
          <form className="flex flex-col gap-4" onSubmit={onSubmit}>
            <TextField fullWidth isRequired name="email" type="email" value={email} onChange={setEmail}>
              <Label>Email</Label>
              <Input placeholder="you@example.com" />
            </TextField>
            <TextField fullWidth isRequired name="password" type="password" value={password} onChange={setPassword}>
              <Label>Password</Label>
              <Input placeholder="At least 8 characters" minLength={8} />
            </TextField>
            {error && (
              <Alert status="danger">
                <Alert.Indicator />
                <Alert.Content>
                  <Alert.Title>{error}</Alert.Title>
                </Alert.Content>
              </Alert>
            )}
            <Button fullWidth type="submit">Create account</Button>
          </form>
        </Card.Content>
        <Card.Footer>
          <span className="text-sm text-gray-600">Have an account? <Link className="text-blue-600" to="/login">Log in</Link></span>
        </Card.Footer>
      </Card>
    </div>
  );
}