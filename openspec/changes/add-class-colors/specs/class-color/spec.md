## Purpose

Give every school class a background color that identifies it in exported timetables. The defaults are distinct and readable, and users can override them.

## ADDED Requirements

### Requirement: Class has a color
Every school class SHALL have a color expressed as a 6-digit hex string (`#rrggbb`). The class API SHALL return the color with each class.

#### Scenario: Listing classes
- **WHEN** a user lists the classes of the active workspace
- **THEN** each returned class includes its `#rrggbb` color

### Requirement: Distinct default color from a readable palette
When a class is created without an explicit color, the system SHALL assign the first color of a fixed palette that no other class in the same workspace uses. The palette SHALL contain at least 30 colors so that every class allowed by the class form (years 1–5, sections A–F) receives a distinct default. Every palette color SHALL have a contrast ratio of at least 4.5:1 against black text. If every palette color is already in use, the system SHALL cycle through the palette again.

#### Scenario: Creating a class in a workspace with existing classes
- **WHEN** a user creates a class and some palette colors are already used by other classes in the workspace
- **THEN** the new class gets the first palette color not used in that workspace

#### Scenario: Colors are isolated per workspace
- **WHEN** a class in another workspace uses a palette color
- **THEN** that color is still available as a default for classes in the active workspace

#### Scenario: Default colors are readable
- **WHEN** any palette color is used as a background for black text
- **THEN** the contrast ratio is at least 4.5:1

### Requirement: Existing classes receive default colors
Classes that existed before this capability SHALL be assigned distinct palette colors within their workspace, following the same default rule in class creation order.

#### Scenario: Upgrading a workspace with classes
- **WHEN** the system is upgraded and a workspace already has classes
- **THEN** every existing class has a color and no two classes in that workspace share a default color

### Requirement: User can change a class color
The system SHALL let a user change a class's color with a color picker on the Classes page. The system SHALL accept a color already used by another class in the workspace, and the Classes page SHALL warn the user when the chosen color duplicates another class's color. The API SHALL reject a color that is not a `#rrggbb` hex string with a validation error.

#### Scenario: Picking a new color
- **WHEN** a user selects a new color for a class on the Classes page
- **THEN** the class's color is saved and shown on subsequent visits

#### Scenario: Picking a duplicate color
- **WHEN** a user selects a color already used by another class in the workspace
- **THEN** the color is saved and the Classes page shows a warning naming the duplicate

#### Scenario: Submitting an invalid color
- **WHEN** a client sends a class color that is not a `#rrggbb` hex string
- **THEN** the API rejects the request with a validation error and does not change the class
