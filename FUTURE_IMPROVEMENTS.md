# Web Dashboard - Future Improvements

This document tracks planned enhancements for the Bonus Points Bot web dashboard.

---

## ðŸ"± Mobile & Responsive Design

### Adaptive Layout for Mobile Devices
**Priority:** High  
**Status:** Planned

**Description:**  
Optimize the dashboard for mobile devices to eliminate the need for alt-tabbing between Discord and browser. Users should be able to manage activities comfortably from their phones.

**Features:**
- Touch-optimized controls (larger checkboxes, buttons)
- Responsive grid layouts that adapt to smaller screens
- Mobile-friendly navigation
- Swipe gestures for quick actions (optional)
- Progressive Web App (PWA) support for "Add to Home Screen"

**Benefits:**
- Users can track activities without switching between apps
- Better accessibility on tablets and phones
- Improved user engagement

---

## ðŸŽ¨ Theme/Style Customization

### User-Selectable Themes
**Priority:** Medium  
**Status:** Planned

**Description:**  
Allow users to select their preferred visual style/theme for the dashboard.

**Potential Themes:**
- Dark Mode (current default)
- Light Mode
- Discord-style theme
- High Contrast mode
- Colorblind-friendly palettes
- Custom accent colors

**Implementation Ideas:**
- Theme switcher in navigation bar
- Store preference in session/database
- CSS variables for easy theme switching
- Preview before applying

**Benefits:**
- Personalization improves user satisfaction
- Accessibility for different visual preferences
- Better usability in different lighting conditions

---

## ðŸ" Search & Filtering

### Activity Search Functionality
**Priority:** Medium  
**Status:** Planned

**Description:**  
Add search/filter capabilities to quickly find specific activities among the 41+ total activities.

**Features:**
- Real-time search as user types
- Filter by category (Solo/Paired)
- Filter by BP value range
- Filter by completion status
- Sort options (alphabetical, BP value, recently completed)
- Quick filters (e.g., "High BP", "Uncompleted Only")

**Benefits:**
- Faster activity location
- Better user experience with large activity lists
- Reduced scrolling on mobile

---

## ✅ Completed Activities Management

### Separate "Completed" Tab
**Priority:** High  
**Status:** Planned

**Description:**  
Move completed activities out of the main view to a separate "Completed" tab, keeping the main dashboard clean and focused on remaining tasks.

**Features:**

**Main Dashboard:**
- Show only uncompleted activities by default
- Clean, uncluttered interface
- More screen space for active tasks
- Visual indicator showing X/41 completed

**Completed Tab:**
- Separate view for all completed activities
- Ability to uncomplete activities (undo mistakes)
- Grouped by category
- Shows BP earned from each
- Optional: completion timestamps

**Toggle Options:**
- Quick button to show/hide completed on main view
- Setting to remember user preference

**Benefits:**
- Reduces visual clutter
- Focuses attention on remaining tasks
- Prevents accidental completion status changes
- Easy recovery from misclicks
- Better mobile experience with less scrolling

---

## Implementation Notes

**Suggested Implementation Order:**
1. **Completed Activities Tab** (High Priority)
   - Immediate UX improvement
   - Reduces screen clutter significantly

2. **Mobile Optimization** (High Priority)
   - Core functionality for many users
   - Foundation for other improvements

3. **Search & Filtering** (Medium Priority)
   - Enhances usability
   - Works well with completed activities separation

4. **Theme Customization** (Medium Priority)
   - Nice-to-have feature
   - Can be added incrementally

**Technical Considerations:**
- All features should maintain database consistency
- Real-time Discord dashboard sync must work with all changes
- Mobile responsiveness testing required for each feature
- User preferences should persist across sessions

---

## Future Ideas (Backlog)

Additional features to consider for later phases:

- **Historical Data:**
  - Weekly/monthly completion charts
  - BP earning trends
  - Activity completion streaks

- **Quick Actions:**
  - Bulk complete/uncomplete
  - Favorite activities for quick access
  - Recent activities list

- **Notifications:**
  - Browser push notifications for daily reset
  - Reminders for uncompleted activities

- **Social Features:**
  - Leaderboards
  - Activity completion sharing
  - Team challenges

---

*Document created: October 28, 2025*  
*Last updated: October 28, 2025*
