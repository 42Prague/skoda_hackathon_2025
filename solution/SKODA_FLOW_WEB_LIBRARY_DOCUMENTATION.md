# ŠKODA Flow Web Library - Complete Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [Theme Provider Setup](#theme-provider-setup)
5. [Components Overview](#components-overview)
6. [Material UI Components](#material-ui-components)
7. [Custom Components](#custom-components)
8. [Styling Guide](#styling-guide)
9. [Theme Customization](#theme-customization)
10. [Accessibility](#accessibility)
11. [Breakpoints](#breakpoints)
12. [Best Practices](#best-practices)
13. [Resources](#resources)

---

## Introduction

**Flow Web Library** is the React implementation of the [ŠKODA Flow Design System](https://skoda-brand.com/hub/26). This package contains a theme for [@mui/material](https://mui.com/material-ui/customization/theming/) as well as completely custom components, designed to simplify development of ŠKODA Auto Web Applications.

### Mission

The library unites React JS components, Design Tokens, and MUI principles with other assets such as logos, icons, and font files. The engineering team works in tandem with Flow DS UI designers to:

- Package React JS web components into an NPM artifact for internal or external developers
- Integrate React JS web components into a private Storybook to showcase interactive UI components

### Package Information

- **NPM Package**: `@skodaflow/web-library`
- **NPM Registry**: Available on public npm repository
- **Framework**: Built on Material UI Framework for React JS
- **Storybook**: [https://skodaflow-web.azurewebsites.net/](https://skodaflow-web.azurewebsites.net/)

---

## Installation

### Install the Package

```bash
npm i @skodaflow/web-library
```

### Peer Dependencies

Peer dependencies should be installed automatically. However, if you need to install them manually:

```bash
npm i @mui/material @emotion/react @emotion/styled react react-dom
```

---

## Getting Started

### 1. Use Theme Provider

In order to use `@skodaflow/web-library`, you must use the `SkodaThemeProvider` component in your main file (usually `main.tsx`, `App.tsx`, or `index.tsx`). This provides the correct theme for the library components.

**Recommended setup with global styling:**

```tsx
import { SkodaThemeProvider } from '@skodaflow/web-library';
import { CssBaseline } from '@mui/material';

function App() {
  return (
    <SkodaThemeProvider globalBaseline>
      <CssBaseline />
      {children}
    </SkodaThemeProvider>
  );
}
```

**Note:** Font files are automatically imported from the `@skodaflow/web-tokens` repository with the import in the theme.

### 2. Use Components

Use components provided by the Flow library and `@mui/material`:

```tsx
import { Typography } from '@skodaflow/web-library';
import { Button, Box } from '@mui/material';

function MyComponent() {
  return (
    <>
      <Typography variant="subheadline">Flow Headline</Typography>
      <Box sx={{ pt: 2 }} />
      <Button>Flow Button</Button>
    </>
  );
}
```

### 3. Next Steps

After setup, we recommend exploring:

1. **Typography** - Learn more about fonts and typography
2. **Palette and Colors** - Discover the color system
3. **Box** - Use as a basic building block
4. **Styling** - Find best practices in the Styling section
5. **Theme Customization** - Check how the theme can be customized
6. **Button** - Press and play with buttons
7. **Icons** - Have a look at all the Flow design icons
8. **Accessibility** - Make sure to review accessibility guidelines

---

## Theme Provider Setup

### SkodaThemeProvider

The `SkodaThemeProvider` is the core component that wraps your application and provides the Flow theme to all child components.

**Props:**
- `globalBaseline` (boolean): Applies global baseline styles
- `theme` (Theme): Optional custom theme object (see Theme Customization)

**Basic Usage:**

```tsx
import { SkodaThemeProvider } from '@skodaflow/web-library';
import { CssBaseline } from '@mui/material';

<SkodaThemeProvider globalBaseline>
  <CssBaseline />
  {children}
</SkodaThemeProvider>
```

---

## Components Overview

The library provides two main categories of components:

### Custom Components

These are Flow-specific components built for ŠKODA applications:

- **Banner** - Display promotional or informational banners
- **BottomSheet** - Mobile-friendly bottom sheet component
- **BypassBlock** - Accessibility component for keyboard navigation
- **Carousel** - Image/content carousel component
- **ErrorContent** - Error state display component
- **Flag** - Country/region flag display
- **FocusRing** - Focus indicator component
- **Footer** - Application footer component
- **Header** - Application header component
- **Icons** - Complete set of Flow design icons
- **Image** - Enhanced image component
- **Label** - Custom label component
- **Logo** - ŠKODA logo component
- **Notification** - Notification/toast component
- **Overlay** - Overlay component for modals/dialogs
- **PageLayout** - Page layout wrapper component
- **PlayPauseButton** - Media playback control button
- **Progress** - Progress indicator component
- **QuickLink** - Quick link component
- **Scrollbar** - Custom scrollbar component
- **Search** - Search input component
- **SecondaryNavigation** - Secondary navigation component
- **SegmentedControls** - Segmented control component
- **Shortcut** - Keyboard shortcut component
- **SkodaThemeProvider** - Theme provider component
- **Spacing** - Spacing utility component
- **TextAndCta** - Text with CTA component
- **Upload** - File upload component
- **Video** - Video player component

### Material UI Components

The library provides styled versions of Material UI components:

- **Accordion** - Expandable content sections
- **Alert** - Alert/notification messages
- **AppBar** - Application bar component
- **Autocomplete** - Autocomplete input field
- **Avatar** - User avatar component
- **Backdrop** - Backdrop overlay component
- **Badge** - Badge indicator component
- **Box** - Basic building block component
- **Breadcrumbs** - Navigation breadcrumbs
- **Button** - Button component (see detailed section below)
- **Card** - Card container component
- **Checkbox** - Checkbox input component
- **Chip** - Chip/tag component
- **Container** - Container wrapper component
- **DatePicker** - Date picker component
- **DateTimePicker** - Date and time picker
- **Dialog** - Dialog/modal component
- **Divider** - Divider line component
- **Drawer** - Side drawer component
- **Fab** - Floating action button
- **IconButton** - Icon-only button
- **Link** - Link component
- **List** - List component
- **Menu** - Menu dropdown component
- **Pagination** - Pagination component
- **Paper** - Paper surface component
- **Radio** - Radio button component
- **Rating** - Rating component
- **Skeleton** - Loading skeleton component
- **Slider** - Slider input component
- **Stepper** - Stepper component
- **SvgIcon** - SVG icon wrapper
- **Switch** - Toggle switch component
- **Table** - Table component
- **Tabs** - Tabs component
- **TextField** - Text input field
- **ThemeProvider** - MUI theme provider
- **TimePicker** - Time picker component
- **Tooltip** - Tooltip component
- **Typography** - Typography component

---

## Material UI Components

### Button

The Button component is a standard MUI Button styled with the Flow theme.

**Import:**

```tsx
import { Button } from '@mui/material';
// or
import { Button } from '@skodaflow/web-library';
```

**Basic Usage:**

```tsx
<Button>Click me</Button>
```

**Variants:**

```tsx
<Button>Primary</Button>
<Button color="surface">Secondary</Button>
<Button variant="text" color="secondary">Tertiary</Button>
<Button variant="outlined" color="secondary">Outline</Button>
<Button color="error">Destructive</Button>
```

**Sizes:**

```tsx
<Button size="small">Compact</Button>
<Button size="medium">Standard</Button> // default
```

**With Icons:**

```tsx
import { HeartIcon } from '@skodaflow/web-library';

<Button startIcon={<HeartIcon />}>Start Icon</Button>
<Button endIcon={<HeartIcon />}>End Icon</Button>
```

**As Link:**

```tsx
<Button 
  component="a" 
  href="https://www.skoda-auto.cz/" 
  target="_blank" 
  rel="noreferrer"
  aria-label="Open the Škoda website in a new tab"
  color="surface"
>
  External Link
</Button>
```

**Navigation Variant:**

```tsx
import { ArrowRightIcon, ArrowLeftIcon } from '@skodaflow/web-library';

<Button variant="navigation" color="secondary" endIcon={<ArrowRightIcon />}>
  Forward
</Button>
<Button variant="navigation" color="secondary" startIcon={<ArrowLeftIcon />}>
  Back
</Button>
```

**Dark Background:**

```tsx
<Box sx={{ color: 'common.white', backgroundColor: 'onSurface.os800' }}>
  <Button variant="outlined" color="white">Outlined</Button>
  <Button variant="text" color="white">Text</Button>
</Box>
```

**Disabled State:**

```tsx
<Button disabled>Disabled Button</Button>
```

### Typography

Typography component with Flow design system variants.

**Usage:**

```tsx
import { Typography } from '@skodaflow/web-library';

<Typography variant="subheadline">Flow Headline</Typography>
```

### Box

The Box component is the basic building block for layout and styling.

**Usage:**

```tsx
import { Box } from '@mui/material';

<Box sx={{ pt: 2, backgroundColor: 'brand.tertiary', color: 'common.white' }}>
  Content
</Box>
```

---

## Custom Components

### BypassBlock

Accessibility component that provides keyboard users with the opportunity to skip to main content.

**Usage:**

```tsx
import { SkodaThemeProvider, BypassBlock } from '@skodaflow/web-library';
import { CssBaseline } from '@mui/material';

<SkodaThemeProvider globalBaseline>
  <CssBaseline />
  <BypassBlock href="#main">Skip to content</BypassBlock>
  {children}
</SkodaThemeProvider>
```

**Note:** Place as the first element in the HTML structure, right after `SkodaThemeProvider`.

### Icons

Complete set of Flow design icons available from the library.

**Usage:**

```tsx
import { HeartIcon, ArrowRightIcon, ArrowLeftIcon } from '@skodaflow/web-library';

<HeartIcon />
<ArrowRightIcon />
<ArrowLeftIcon />
```

View all available icons in the Storybook: [All Icons](https://skodaflow-web.azurewebsites.net/?path=/story/web-library-components-icons--all-icons)

---

## Styling Guide

### Why sx?

The `sx` property comes with several advantages:

- No need to name classes (no more `.wrappers` and `.holders`)
- Easy access to component properties and theme via theme-aware properties
- Code and style in the same place (when components are properly split)
- Generates classes in the background (similar to `styled()` solution)
- Can target other elements

**Basic Usage:**

```tsx
<Box sx={{
  // child @mui button
  '& .MuiButton-root': {
    // styles
  }
}} />
```

### Utilize Theme Properties

With `sx`, you have access to the theme which contains the Palette with all necessary colors.

**Using Shortcuts:**

```tsx
<Box sx={{
  backgroundColor: 'brand.tertiary',
  color: 'common.white',
  p: 2
}} />

// Same as above
<Box sx={{
  backgroundColor: (theme) => theme.palette.brand.tertiary,
  color: (theme) => theme.palette.common.white,
  padding: (theme) => theme.spacing(2)
}} />
```

### Media Queries

Via `sx` property, you can quickly access media query breakpoints.

**Flow Breakpoints:**
- `xs` (extra-small): 0px - 359px
- `sm` (small): 360px - 719px
- `md` (medium): 720px - 1079px
- `lg` (large): 1080px - 1439px
- `xl` (extra-large): 1440px+

**Responsive Styling:**

```tsx
<Box sx={{
  backgroundColor: {
    // mobile
    xs: 'brand.primary',
    // tablet+
    md: 'onSurface.os800',
  }
}} />
```

**Theme Customization with Media Queries:**

```tsx
styleOverrides: {
  root: ({ theme }) => ({
    [theme.breakpoints.up('xs')]: {
      fontWeight: '400',
    },
  }),
}
```

### Style Priority with Multiple Ampersands

When styling via `sx` has lower priority (e.g., when parent styling targets children), use multiple ampersands `&&` to gain higher priority instead of `!important`.

**Example:**

```tsx
<Box sx={{ '& div': { color: 'error.main' } }}>
  <Box sx={{ '&&': { color: 'success.main' } }}>
    Text is now green
  </Box>
</Box>
```

**Best Practice:** Directly style components themselves instead of wrappers to avoid this issue.

---

## Theme Customization

`@skodaflow/web-library` comes with a fully styled `@mui/material` theme. You can override defaults or customize options to fit your application needs.

### Theme Composition

It is recommended to use theme composition for overrides.

**Example:**

```tsx
import { SkodaThemeProvider, theme } from '@skodaflow/web-library';
import { CssBaseline } from '@mui/material';
import { createTheme } from '@mui/material/styles';

const customTheme = createTheme(theme, {
  components: {
    MuiTabs: {
      defaultProps: {
        template: 'underlined',
      },
    },
    MuiIconButton: {
      defaultProps: {
        size: 'medium',
      },
    },
  },
});

function App() {
  return (
    <SkodaThemeProvider globalBaseline theme={customTheme}>
      <CssBaseline />
      {children}
    </SkodaThemeProvider>
  );
}
```

### Utilize Theme Properties

We recommend using colors and other properties from the exposed theme.

**Important:** Make sure to include existing styling from the library.

```tsx
import { theme } from '@skodaflow/web-library';
import { createTheme } from '@mui/material/styles';

const customTheme = createTheme(theme, {
  components: {
    MuiAlert: {
      styleOverrides: {
        ...theme.components?.MuiAlert?.styleOverrides,
        root: [
          theme.components?.MuiAlert?.styleOverrides?.root,
          {
            padding: `${theme.spacing(2)} ${theme.spacing(4)}`,
            backgroundColor: theme.palette.common.white,
            color: theme.palette.primary.main,
          },
        ],
      },
    },
  },
});
```

### Extend Global Styling

You can extend global styling by modifying `CssBaseline` or `ScopedCssBaseline`.

**Important:** Make sure to provide initial value from the theme, otherwise the global style from Flow Library will be overwritten instead of extended.

```tsx
import { theme } from '@skodaflow/web-library';
import { createTheme } from '@mui/material/styles';

const customTheme = createTheme(theme, {
  components: {
    MuiCssBaseline: {
      styleOverrides: [
        theme.components?.MuiCssBaseline?.styleOverrides,
        {
          '*, *:before, *:after': {
            boxSizing: 'border-box',
            maxWidth: '100%',
            minWidth: '0',
            minHeight: '0',
          },
          'html, body, #root': {
            height: '100%',
          },
        }
      ]
    }
  }
});
```

### Overwriting Font Style

Since version `v7.0.0`, font styling is done using `@media` and `@container` queries for responsive typography. Use `@media` queries for overwriting as well, as a regular class selector is not sufficient due to CSS selector specificity.

**At Theme Level:**

```tsx
import { theme } from '@skodaflow/web-library';
import { createTheme } from '@mui/material/styles';

const customTheme = createTheme(theme, {
  typography: {
    h2: {
      [theme.breakpoints.up('xs')]: {
        fontSize: '12px',
      },
    },
  },
});
```

**At Component Level:**

```tsx
import { Typography } from '@skodaflow/web-library';

<Typography variant="h1" sx={{ fontSize: { xs: '12px' } }}>
  Small Font Headline
</Typography>
```

### Deprecated SkodaThemeWidgetProvider

As the `SkodaThemeWidgetProvider` generates its theme on each container or window resize, to customize the theme, you need to provide just the overwrites.

```tsx
import { SkodaThemeWidgetProvider } from '@skodaflow/web-library';

const themeOverwrites = {
  components: {
    MuiButton: {
      defaultProps: {
        variant: 'outlined'
      }
    }
  }
};

function Component() {
  return (
    <SkodaThemeWidgetProvider theme={themeOverwrites}>
      {children}
    </SkodaThemeWidgetProvider>
  );
}
```

---

## Accessibility

`@skodaflow/web-library` follows accessibility standards and guidelines to ensure digital content is accessible to all users. The library complies with the European accessibility act.

### Bypass Block

Each website with introduction or repeated content should contain `BypassBlock`, which provides keyboard users with the opportunity to go straight to the content of the page.

**Placement:** Place as the first element in the HTML structure, right after `SkodaThemeProvider`.

```tsx
import { SkodaThemeProvider, BypassBlock } from '@skodaflow/web-library';
import { CssBaseline } from '@mui/material';

<SkodaThemeProvider globalBaseline>
  <CssBaseline />
  <BypassBlock href="#main">Skip to content</BypassBlock>
  {children}
</SkodaThemeProvider>
```

### Images alt

Each image must provide an `alt` attribute with alternate text. Provide an empty string `alt=""` for decorative images.

```tsx
import { Box } from '@mui/material';

<Box component="img" src="/assets/kodiaq.jpg" alt="Škoda Kodiaq" />
```

### Link's and Button's aria-label

Components without clear description labels must contain `aria-label`. This affects all `IconButtons` and `Fabs`.

```tsx
import { IconButton } from '@mui/material';
import { HeartIcon } from '@skodaflow/web-library';

<IconButton aria-label="Add to Favorites">
  <HeartIcon />
</IconButton>
```

Each link without explicit text (like 'Read more') should contain an `aria-label` with a more descriptive label.

```tsx
import { Button } from '@mui/material';

<Button 
  color="surface" 
  href="https://www.skoda-auto.com/models/range/enyaq" 
  aria-label="Read more about Škoda Enyaq"
>
  Read more
</Button>
```

This might also be the case for clickable `Banner`, `Card`, `QuickLink`, and other interactive elements.

### Selectable Components

Interactive selectable components (e.g., `List`, `Menu`, `Card`) should contain proper `role` and `aria-selected`.

- Use `role="radio"` for single-select options
- Use `role="checkbox"` for multi-select options
- Add `aria-selected` to selected components

```tsx
import { List, ListItem, ListItemButton, ListItemText } from '@mui/material';

<List role="radio">
  <ListItem>
    <ListItemButton selected={true} aria-selected={true}>
      <ListItemText primary="Title" secondary="Description" />
    </ListItemButton>
  </ListItem>
</List>
```

### Tabs Controls

`Tabs` controlling appearance of content should contain `aria-controls` tag.

- Provide `id` and `aria-controls` properties to each `Tab`
- Provide `id` and `aria-labeledby` to each `TabPanel`

```tsx
import { Tabs, Tab } from '@mui/material';
import { TabPanel } from '@skodaflow/web-library';

<Tabs>
  <Tab 
    value={index} 
    label="..." 
    id={`tab-${index}`} 
    aria-controls={`tabpanel-${index}`}
  />
</Tabs>
<TabPanel 
  index={index} 
  value={tab} 
  id={`tabpanel-${index}`} 
  aria-labeledby={`tab-${index}`}
>
  ...
</TabPanel>
```

### Errors

Form errors must be clearly indicated. Just a change of color is insufficient.

- `TextField` with the `error` property adds an error icon into helper text automatically
- `Checkbox` and `Radio` with `error` property should be accompanied by a clearly visible error message using `FormMessage` or `Banner` components

```tsx
import { FormMessage } from '@skodaflow/web-library';

<FormControl error>
  <FormLabel>...</FormLabel>
  <FormMessage>Select at least one option from the list below</FormMessage>
  <FormGroup>
    ...
  </FormGroup>
</FormControl>
```

### Interactive Components

Every clickable element must follow guidelines regarding keyboard navigation and visual effects. The `@skodaflow/web-library` follows these guidelines for every component by default, so no additional steps are required from developers.

---

## Breakpoints

The Flow design system uses the following breakpoints:

- **xs** (extra-small): 0px - 359px
- **sm** (small): 360px - 719px
- **md** (medium): 720px - 1079px
- **lg** (large): 1080px - 1439px
- **xl** (extra-large): 1440px+

**Usage in sx:**

```tsx
<Box sx={{
  fontSize: {
    xs: '14px',  // mobile
    md: '16px',  // tablet
    lg: '18px',  // desktop
  }
}} />
```

**Usage in Theme:**

```tsx
styleOverrides: {
  root: ({ theme }) => ({
    [theme.breakpoints.up('xs')]: {
      // styles
    },
    [theme.breakpoints.down('md')]: {
      // styles
    },
  }),
}
```

---

## Best Practices

### 1. Component Import

Import components from `@skodaflow/web-library` for custom components, and from `@mui/material` for Material UI components (both work, but this is the recommended approach).

```tsx
// Custom Flow components
import { Typography, Banner, Icons } from '@skodaflow/web-library';

// Material UI components
import { Button, Box, TextField } from '@mui/material';
```

### 2. Use Box for Layout

Use the `Box` component as the basic building block for layout and styling instead of `div` elements.

```tsx
<Box sx={{ p: 2, backgroundColor: 'background.paper' }}>
  Content
</Box>
```

### 3. Theme-Aware Styling

Always use theme properties for colors, spacing, and other design tokens.

```tsx
// Good
<Box sx={{ color: 'primary.main', p: 2 }} />

// Avoid
<Box sx={{ color: '#FF0000', padding: '16px' }} />
```

### 4. Responsive Design

Always consider responsive design using breakpoints.

```tsx
<Box sx={{
  padding: {
    xs: 1,
    md: 2,
    lg: 3,
  }
}} />
```

### 5. Accessibility First

- Always include `BypassBlock` for keyboard navigation
- Provide `alt` text for images
- Use `aria-label` for icon-only buttons
- Ensure proper form error messaging
- Use semantic HTML and ARIA attributes

### 6. Component Composition

Compose complex UIs from smaller, reusable components.

```tsx
function CardWithAction({ title, description, action }) {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6">{title}</Typography>
        <Typography variant="body2">{description}</Typography>
      </CardContent>
      <CardActions>
        <Button>{action}</Button>
      </CardActions>
    </Card>
  );
}
```

### 7. Theme Customization

When customizing the theme, always extend existing styles rather than replacing them.

```tsx
// Good - extends existing styles
const customTheme = createTheme(theme, {
  components: {
    MuiButton: {
      styleOverrides: {
        ...theme.components?.MuiButton?.styleOverrides,
        root: {
          // additional styles
        },
      },
    },
  },
});
```

---

## Resources

### Official Documentation

- **Storybook**: [https://skodaflow-web.azurewebsites.net/](https://skodaflow-web.azurewebsites.net/)
- **Flow Design System**: [https://flow.skoda-brand.com](https://flow.skoda-brand.com)
- **NPM Package**: [@skodaflow/web-library](https://www.npmjs.com/package/@skodaflow/web-library)
- **Material UI Documentation**: [https://mui.com/material-ui/getting-started/overview/](https://mui.com/material-ui/getting-started/overview/)

### Internal Resources

- **ŠA Wiki**: [https://wiki.skoda.vwgroup.com/spaces/FWL/overview](https://wiki.skoda.vwgroup.com/spaces/FWL/overview) - Guidance on how best to integrate the NPM package

### Contact

If your team needs new components (or upgrades to existing ones), especially components that are worthy of being part of the library, or if you have any other questions, please contact:

- **Email**: [flow@skoda-auto.cz](mailto:flow@skoda-auto.cz)

### Additional Links

- **Typography Guide**: [Storybook - Typography](https://skodaflow-web.azurewebsites.net/?path=/story/web-library-material-ui-typography--docs)
- **Palette and Colors**: [Storybook - Palette](https://skodaflow-web.azurewebsites.net/?path=/story/web-library-material-ui-palette-and-colors--docs)
- **All Icons**: [Storybook - Icons](https://skodaflow-web.azurewebsites.net/?path=/story/web-library-components-icons--all-icons)
- **Interactive Components Guide**: [Storybook - Interactive Components](https://skodaflow-web.azurewebsites.net/?path=/docs/how-to-interactive-components--docs)
- **Minimizing Bundle Size**: [Storybook - Bundle Size](https://skodaflow-web.azurewebsites.net/?path=/docs/how-to-minimizing-bundle-size--docs)
- **Right-to-left Support**: [Storybook - RTL](https://skodaflow-web.azurewebsites.net/?path=/docs/how-to-right-to-left-support--docs)

---

## Summary

The ŠKODA Flow Web Library provides a comprehensive set of React components and Material UI theme customization for building ŠKODA Auto web applications. By following this documentation, you can:

1. ✅ Install and set up the library in your project
2. ✅ Use the theme provider correctly
3. ✅ Utilize both custom and Material UI components
4. ✅ Style components using the `sx` property and theme
5. ✅ Customize the theme to fit your needs
6. ✅ Ensure accessibility compliance
7. ✅ Follow best practices for responsive design

For the most up-to-date information and interactive examples, always refer to the [Storybook documentation](https://skodaflow-web.azurewebsites.net/).

---

*Last Updated: Based on Storybook documentation as of 2025*
*Documentation Source: [https://skodaflow-web.azurewebsites.net/](https://skodaflow-web.azurewebsites.net/)*

