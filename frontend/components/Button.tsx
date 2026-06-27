import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean;
  variant?: "primary" | "danger" | "secondary";
}

export default function Button({
  children,
  loading,
  variant = "primary",
  className = "",
  ...props
}: ButtonProps) {
  const baseStyles = "px-4 py-2 text-sm font-bold rounded-lg transition disabled:opacity-50 flex items-center justify-center";
  
  const variants = {
    primary: "text-white bg-indigo-600 hover:bg-indigo-700",
    danger: "text-red-700 bg-red-50 border border-red-200 hover:bg-red-100",
    secondary: "text-slate-700 bg-slate-50 border border-slate-200 hover:bg-slate-100",
  };

  return (
    <button
      {...props}
      disabled={loading || props.disabled}
      className={`${baseStyles} ${variants[variant]} ${className}`}
    >
      {loading ? "Processing..." : children}
    </button>
  );
}