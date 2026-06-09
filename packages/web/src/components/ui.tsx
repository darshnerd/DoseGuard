import { Card, Chip } from "@heroui/react";
import { animate, motion, useMotionValue, useTransform } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { useEffect, type ReactNode } from "react";

export type HeroColor = "danger" | "warning" | "accent" | "success" | "default";

export function severityColor(severity: string): HeroColor {
  switch (severity) {
    case "contraindicated":
    case "severe":
      return "danger";
    case "moderate":
      return "warning";
    case "low":
      return "accent";
    default:
      return "default";
  }
}

export function SeverityChip({ severity }: { severity: string }) {
  return (
    <Chip color={severityColor(severity)} size="sm" variant="soft">
      {severity}
    </Chip>
  );
}

export const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" } },
};

export const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } },
};

export function Stagger({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <motion.div variants={stagger} initial="hidden" animate="show" className={className}>
      {children}
    </motion.div>
  );
}

/** Single fade-up item (page sections, cards). */
export function FadeItem({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <motion.div variants={fadeUp} className={className}>
      {children}
    </motion.div>
  );
}

/** Animated count-up number. */
export function AnimatedNumber({ value, className }: { value: number; className?: string }) {
  const mv = useMotionValue(0);
  const rounded = useTransform(mv, (v) => Math.round(v));
  useEffect(() => {
    const controls = animate(mv, value, { duration: 0.8, ease: "easeOut" });
    return controls.stop;
  }, [value, mv]);
  return <motion.span className={className}>{rounded}</motion.span>;
}

/* ── Page header with icon ── */
export function PageHeader({
  icon: Icon,
  title,
  subtitle,
}: {
  icon: LucideIcon;
  title: string;
  subtitle?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex items-center gap-3"
    >
      <div className="flex size-11 items-center justify-center rounded-2xl bg-brand-soft text-brand">
        <Icon className="size-5" />
      </div>
      <div>
        <h1 className="text-2xl font-bold leading-tight">{title}</h1>
        {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
      </div>
    </motion.div>
  );
}

/* ── Animated stat card ── */
export function Stat({
  icon: Icon,
  label,
  value,
  accent,
}: {
  icon?: LucideIcon;
  label: string;
  value: number | string;
  accent?: string;
}) {
  return (
    <FadeItem>
      <Card className="transition-shadow hover:shadow-md">
        <Card.Content>
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">{label}</div>
            {Icon && <Icon className="size-4 text-gray-400" />}
          </div>
          <div className={`mt-1 text-3xl font-bold ${accent ?? "text-gray-900"}`}>
            {typeof value === "number" ? <AnimatedNumber value={value} /> : value}
          </div>
        </Card.Content>
      </Card>
    </FadeItem>
  );
}
