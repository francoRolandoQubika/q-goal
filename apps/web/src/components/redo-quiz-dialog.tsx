import { ConfirmDialog } from "@q-goal/ui/components/dialog";

interface RedoQuizDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
}

export function RedoQuizDialog({ open, onOpenChange, onConfirm }: RedoQuizDialogProps) {
  return (
    <ConfirmDialog
      open={open}
      onOpenChange={onOpenChange}
      onConfirm={onConfirm}
      title="Redo quiz?"
      description="This clears your current figurita and starts a fresh quiz."
      confirmLabel="Redo quiz"
      cancelLabel="Cancel"
      destructive
    />
  );
}
