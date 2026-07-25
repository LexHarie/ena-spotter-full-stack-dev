import * as AccordionPrimitive from "@radix-ui/react-accordion";
import { ChevronDown } from "lucide-react";
import type { ReactNode } from "react";

interface Props {
  title: string;
  children: ReactNode;
}

export function Accordion({ title, children }: Props) {
  return (
    <AccordionPrimitive.Root type="single" collapsible>
      <AccordionPrimitive.Item value="content" className="accordion-item">
        <AccordionPrimitive.Header>
          <AccordionPrimitive.Trigger className="accordion-trigger">
            {title}
            <ChevronDown aria-hidden="true" size={17} />
          </AccordionPrimitive.Trigger>
        </AccordionPrimitive.Header>
        <AccordionPrimitive.Content className="accordion-content">
          {children}
        </AccordionPrimitive.Content>
      </AccordionPrimitive.Item>
    </AccordionPrimitive.Root>
  );
}
