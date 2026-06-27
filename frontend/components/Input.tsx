import React from "react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
}

export default function Input({ label, ...props }: InputProps) {
  return (
    <div>
      <label className="block text-sm font-semibold text-slate-700 mb-1">
        {label}
      </label>
      <input
        {...props}
        className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition text-slate-800"
      />
    </div>
  );
}