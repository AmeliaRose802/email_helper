# Email Helper Icon Assets

Place your application icons in this directory:

## Required Icons

### Windows
- `icon.ico` - Windows application icon (256x256 or multi-size)
- `icon.png` - Base icon for system tray (256x256 recommended)

### macOS
- `icon.icns` - macOS application icon (1024x1024 base)

### Linux
- `icon.png` - Linux application icon (512x512 recommended)

## Icon Creation Tools

### Online Tools
- [iconverticons.com](https://iconverticons.com/online/) - Convert PNG to ICO/ICNS
- [cloudconvert.com](https://cloudconvert.com/) - Multi-format converter

### CLI Tools
```bash
# Install electron-icon-builder
npm install -g electron-icon-builder

# Generate all icons from a single PNG (1024x1024)
electron-icon-builder --input=./icon-source.png --output=./assets
```

### Manual Creation

**Windows ICO:**
- Use GIMP or Photoshop
- Export as .ico with multiple sizes (16, 32, 48, 64, 128, 256)

**macOS ICNS:**
- Use `iconutil` on macOS:
  ```bash
  mkdir icon.iconset
  sips -z 16 16     icon-1024.png --out icon.iconset/icon_16x16.png
  sips -z 32 32     icon-1024.png --out icon.iconset/icon_16x16@2x.png
  sips -z 32 32     icon-1024.png --out icon.iconset/icon_32x32.png
  # ... (repeat for all sizes)
  iconutil -c icns icon.iconset
  ```

## Current Status

⚠️ **Placeholder icons needed**

The application will build and run without custom icons (using Electron defaults), but for distribution you should:

1. Create or obtain a 1024x1024 PNG icon for Email Helper
2. Convert to required formats (.ico, .icns)
3. Place in this directory
4. Rebuild the application

## Icon Design Tips

- Use simple, recognizable imagery
- Ensure it looks good at small sizes (16x16)
- Use high contrast for visibility
- Avoid too much detail
- Test on both light and dark backgrounds
- Consider the Windows taskbar, macOS dock, and system tray appearances

## Attribution

If using icons from icon libraries, ensure proper attribution and licensing.
