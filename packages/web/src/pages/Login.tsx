import { Alert, Button, Input, Label, TextField } from "@heroui/react";
import { motion } from "framer-motion";
import { ShieldCheck, Sparkles } from "lucide-react";
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
        <h2 className="text-3xl font-bold leading-tight">Take your meds with confidence.</h2>
        <p className="mt-3 max-w-sm text-white/80">
          Scan labels, catch dangerous interactions, and never miss a dose — all in one place.
        </p>
        <ul className="mt-6 space-y-2 text-sm text-white/90">
          {["Interaction checking on every med", "Daily dose tracking & adherence", "OCR label scanning"].map(
            (t) => (
              <li key={t} className="flex items-center gap-2">
                <Sparkles className="size-4" /> {t}
              </li>
            )
          )}
        </ul>
      </div>
      <span className="text-xs text-white/60">Your data stays private.</span>
    </div>
  );
}

export default function Login() {
  const { login } = useAuth();
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
          <h1 className="text-2xl font-bold">Welcome back</h1>
          <p className="mt-1 text-sm text-gray-500">Log in to check your medications.</p>
          <form className="mt-6 flex flex-col gap-4" onSubmit={onSubmit}>
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
            <Button fullWidth type="submit" isPending={loading}>
              {loading ? "Logging in…" : "Log in"}
            </Button>
          </form>
          <p className="mt-6 text-sm text-gray-600">
            No account?{" "}
            <Link className="font-medium text-brand hover:underline" to="/register">
              Register
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
