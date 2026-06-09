import { Alert, Button, Input, Label, TextField } from "@heroui/react";
import { motion } from "framer-motion";
import { HeartPulse, ShieldCheck } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

function BrandPanel() {
  return (
    <div className="bg-brand-gradient relative hidden flex-col justify-between p-10 text-white md:flex">
      <div className="flex items-center gap-2 text-xl font-bold">
        <ShieldCheck className="size-6" /> DoseGuard
      </div>
      <div>
        <HeartPulse className="mb-4 size-10 text-white/90" />
        <h2 className="text-3xl font-bold leading-tight">Start tracking safely.</h2>
        <p className="mt-3 max-w-sm text-white/80">
          Build your medication list once — DoseGuard watches for interactions and keeps your daily
          routine on track.
        </p>
      </div>
      <span className="text-xs text-white/60">Free to use. No card required.</span>
    </div>
  );
}

export default function Register() {
  const { register, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(email, password);
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="grid w-full max-w-4xl overflow-hidden rounded-2xl bg-white shadow-xl md:grid-cols-2"
      >
        <BrandPanel />
        <div className="p-8 sm:p-10">
          <h1 className="text-2xl font-bold">Create your account</h1>
          <p className="mt-1 text-sm text-gray-500">Start tracking your medications safely.</p>
          <form className="mt-6 flex flex-col gap-4" onSubmit={onSubmit}>
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
            <Button fullWidth type="submit" isPending={loading}>
              {loading ? "Creating…" : "Create account"}
            </Button>
          </form>
          <p className="mt-6 text-sm text-gray-600">
            Have an account?{" "}
            <Link className="font-medium text-brand hover:underline" to="/login">
              Log in
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
