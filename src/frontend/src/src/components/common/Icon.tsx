import { LucideIcon } from 'lucide-react';

interface IconProps {
  as: LucideIcon;
  w?: number | string;
  h?: number | string;
  color?: string;
  size?: number;
  [key: string]: any;
}

export const Icon = ({ as: IconComponent, w, h, color, size, ...props }: IconProps) => {
  // Use size prop if provided, otherwise use w or h, default to 16
  const iconSize = size || w || h || 16;
  const numSize = typeof iconSize === 'string' ? parseInt(iconSize) : iconSize;
  
  return <IconComponent size={numSize} color={color} {...props} />;
};

