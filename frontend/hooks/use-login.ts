"use client";

import { useState, useCallback } from "react";

export type LoginState =
  | "idle"
  | "validating"
  | "booting"
  | "success"
  | "redirect"
  | "error";

export interface LoginForm {
  email: string;
  password: string;
  orgCode: string;
  rememberMe: boolean;
}

export interface BootStep {
  label: string;
  status: "pending" | "active" | "done";
}

const BOOT_STEPS: string[] = [
  "Connecting to Organization...",
  "Loading Decision Memories...",
  "Synchronizing GitHub...",
  "Connecting Jira...",
  "Initializing Knowledge Graph...",
  "Preparing AI Assistant...",
];

export function useLogin() {
  const [state, setState] = useState<LoginState>("idle");
  const [form, setForm] = useState<LoginForm>({
    email: "",
    password: "",
    orgCode: "",
    rememberMe: false,
  });
  const [errors, setErrors] = useState<Partial<Record<keyof LoginForm, string>>>({});
  const [bootSteps, setBootSteps] = useState<BootStep[]>(
    BOOT_STEPS.map((label) => ({ label, status: "pending" }))
  );
  const [currentBootStep, setCurrentBootStep] = useState(0);

  const updateField = useCallback(
    (field: keyof LoginForm, value: string | boolean) => {
      setForm((prev) => ({ ...prev, [field]: value }));
      // Clear error on edit
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    },
    []
  );

  const validate = useCallback((): boolean => {
    const newErrors: Partial<Record<keyof LoginForm, string>> = {};

    if (!form.email) {
      newErrors.email = "Work email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      newErrors.email = "Enter a valid email address";
    }

    if (!form.password) {
      newErrors.password = "Password is required";
    } else if (form.password.length < 6) {
      newErrors.password = "Password must be at least 6 characters";
    }

    if (!form.orgCode) {
      newErrors.orgCode = "Organization code is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [form]);

  const runBootSequence = useCallback(async () => {
    setState("booting");

    // Reset all steps
    const steps = BOOT_STEPS.map((label) => ({
      label,
      status: "pending" as const,
    }));
    setBootSteps(steps);
    setCurrentBootStep(0);

    for (let i = 0; i < steps.length; i++) {
      setCurrentBootStep(i);
      // Mark current step active
      setBootSteps((prev) =>
        prev.map((s, idx) =>
          idx === i ? { ...s, status: "active" } : s
        )
      );

      // Simulate processing time (700–1400ms per step)
      await new Promise((r) => setTimeout(r, 700 + Math.random() * 700));

      // Mark done
      setBootSteps((prev) =>
        prev.map((s, idx) =>
          idx === i ? { ...s, status: "done" } : s
        )
      );
    }

    // Small pause before success
    await new Promise((r) => setTimeout(r, 600));
    setState("success");

    // Auto-redirect after 4 seconds
    setTimeout(() => {
      setState("redirect");
    }, 4000);
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!validate()) return;

    setState("validating");

    // Simulate auth API call
    await new Promise((r) => setTimeout(r, 800));

    // Start boot sequence
    runBootSequence();
  }, [validate, runBootSequence]);

  const resetState = useCallback(() => {
    setState("idle");
    setErrors({});
    setBootSteps(BOOT_STEPS.map((label) => ({ label, status: "pending" })));
    setCurrentBootStep(0);
  }, []);

  return {
    state,
    form,
    errors,
    bootSteps,
    currentBootStep,
    updateField,
    handleSubmit,
    resetState,
  };
}
