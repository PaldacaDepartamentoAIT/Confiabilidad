export const en = {
  app: {
    title: "Reliability — Components",
    heading: "Reliability",
    intro: "Preview of the shared components for the industrial asset management screens.",
  },
  language: {
    label: "Language",
  },
  button: {
    processing: "Processing…",
    processingAnnouncement: "Processing",
  },
  field: {
    requiredLegend: "Fields marked with * are required.",
    showPassword: "Show password",
    newPasswordHint: "At least 12 characters, not only numbers.",
  },
  message: {
    error: "Error:",
    success: "Success:",
    info: "Information:",
  },
  validation: {
    required: "Fill in this field.",
    email: "Enter an email like name@company.com.",
    codeIncomplete: "Enter all 6 digits of the code.",
    tooManyAttempts: "Too many attempts. Wait a few minutes and try again.",
    serverError: "Something went wrong on our server. Try again in a few minutes.",
    passwordTooShort: "Use at least 12 characters.",
    passwordOnlyDigits: "Don't use only numbers.",
  },
  showcase: {
    formTitle: "Sample form",
    nameLabel: "Full name",
    emailLabel: "Email",
    passwordLabel: "Password",
    newPasswordLabel: "New password",
    codeLabel: "Verification code",
    submit: "Verify",
    showExampleError: "Show sample general error",
    demoInfo: "Demo form: no data is sent.",
  },
};

export type Messages = typeof en;
