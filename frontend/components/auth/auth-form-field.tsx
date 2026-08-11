"use client";

import type { UseFormRegisterReturn } from "react-hook-form";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

/** Labelled auth input with inline validation message. */
export function AuthFormField({
  error,
  label,
  name,
  placeholder,
  registration,
  type
}: {
  error?: string;
  label: string;
  name: string;
  placeholder: string;
  registration: UseFormRegisterReturn;
  type?: string;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={name}>{label}</Label>
      <Input id={name} type={type} placeholder={placeholder} {...registration} />
      {error ? <p className="text-sm text-red-500">{error}</p> : null}
    </div>
  );
}
