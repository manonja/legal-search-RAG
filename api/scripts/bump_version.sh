#!/bin/bash
# Script to bump version numbers in the VERSION file

set -e

VERSION_FILE="VERSION"

function get_version() {
    cat "$VERSION_FILE"
}

function bump_major() {
    current=$(get_version)
    major=$(echo "$current" | cut -d. -f1)
    new_version="$((major + 1)).0.0"
    echo "$new_version" > "$VERSION_FILE"
    echo "Version bumped from $current to $new_version"
}

function bump_minor() {
    current=$(get_version)
    major=$(echo "$current" | cut -d. -f1)
    minor=$(echo "$current" | cut -d. -f2)
    new_version="$major.$((minor + 1)).0"
    echo "$new_version" > "$VERSION_FILE"
    echo "Version bumped from $current to $new_version"
}

function bump_patch() {
    current=$(get_version)
    major=$(echo "$current" | cut -d. -f1)
    minor=$(echo "$current" | cut -d. -f2)
    patch=$(echo "$current" | cut -d. -f3)
    new_version="$major.$minor.$((patch + 1))"
    echo "$new_version" > "$VERSION_FILE"
    echo "Version bumped from $current to $new_version"
}

case "$1" in
    major)
        bump_major
        ;;
    minor)
        bump_minor
        ;;
    patch)
        bump_patch
        ;;
    *)
        echo "Usage: $0 {major|minor|patch}"
        echo "Current version: $(get_version)"
        exit 1
        ;;
esac

exit 0
