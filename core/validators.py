import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class ComplexPasswordValidator:
    """
    Validates that a password contains at least:
    - 1 uppercase letter
    - 1 lowercase letter
    - 1 digit
    - 1 special character
    """

    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter."),
                code='password_no_upper',
            )
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("Password must contain at least one lowercase letter."),
                code='password_no_lower',
            )
        if not re.search(r'\d', password):
            raise ValidationError(
                _("Password must contain at least one digit."),
                code='password_no_digit',
            )
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                _("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)."),
                code='password_no_special',
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least one uppercase letter, "
            "one lowercase letter, one digit, and one special character."
        )


def validate_json_structure(value, required_keys=None):
    """Validate JSON field structure"""
    if not isinstance(value, dict):
        raise ValidationError("Value must be a JSON object (dictionary).")

    if required_keys:
        missing_keys = set(required_keys) - set(value.keys())
        if missing_keys:
            raise ValidationError(f"Missing required keys: {', '.join(missing_keys)}")


def validate_url_list(value):
    """Validate that value is a list of valid URLs"""
    if not isinstance(value, list):
        raise ValidationError("Value must be a list.")

    from django.core.validators import URLValidator
    url_validator = URLValidator()

    for i, url in enumerate(value):
        try:
            url_validator(url)
        except ValidationError:
            raise ValidationError(f"Invalid URL at position {i}: {url}")


def validate_platform_list(value):
    """Validate platform choices"""
    if not isinstance(value, list):
        raise ValidationError("Value must be a list.")

    valid_platforms = ['facebook', 'instagram', 'twitter', 'linkedin', 'youtube', 'tiktok', 'wordpress', 'email', 'other']

    for platform in value:
        if platform not in valid_platforms:
            raise ValidationError(f"Invalid platform: {platform}. Valid options: {', '.join(valid_platforms)}")


def validate_css_selectors(value):
    """Validate CSS selectors"""
    if not isinstance(value, dict):
        raise ValidationError("CSS selectors must be a dictionary.")

    # Basic validation for common CSS selector patterns
    css_pattern = re.compile(r'^[a-zA-Z0-9\-_\.\#\[\]=":,\s>+~\(\)]+$')

    for key, selector in value.items():
        if not isinstance(selector, str):
            raise ValidationError(f"Selector for '{key}' must be a string.")

        if not css_pattern.match(selector):
            raise ValidationError(f"Invalid CSS selector for '{key}': {selector}")


def validate_api_key_format(value):
    """Validate API key format"""
    if not isinstance(value, str):
        raise ValidationError("API key must be a string.")

    # Common API key patterns
    patterns = [
        r'^sk-[a-zA-Z0-9]{48,}$',  # OpenAI style
        r'^AIza[a-zA-Z0-9_-]{35}$',  # Google API key style
        r'^[a-fA-F0-9]{32,64}$',  # Generic hex key
        r'^[a-zA-Z0-9_-]{20,100}$',  # Generic base64-like key
    ]

    if not any(re.match(pattern, value) for pattern in patterns):
        raise ValidationError("Invalid API key format.")


def validate_image_dimensions(width, height):
    """Validate image dimensions"""
    if width < 100 or height < 100:
        raise ValidationError("Image dimensions must be at least 100x100 pixels.")

    if width > 4096 or height > 4096:
        raise ValidationError("Image dimensions cannot exceed 4096x4096 pixels.")

    # Common aspect ratios
    aspect_ratio = width / height
    valid_ratios = [
        (1, 1),    # Square
        (16, 9),   # Widescreen
        (4, 3),    # Standard
        (3, 4),    # Portrait
        (9, 16),   # Mobile portrait
    ]

    tolerance = 0.1
    valid = False
    for w, h in valid_ratios:
        target_ratio = w / h
        if abs(aspect_ratio - target_ratio) <= tolerance:
            valid = True
            break

    if not valid:
        raise ValidationError("Image must have a standard aspect ratio (1:1, 16:9, 4:3, 3:4, or 9:16).")


def validate_content_length(value, min_length=10, max_length=50000):
    """Validate content length"""
    if len(value) < min_length:
        raise ValidationError(f"Content must be at least {min_length} characters long.")

    if len(value) > max_length:
        raise ValidationError(f"Content cannot exceed {max_length} characters.")


def validate_tags_list(value):
    """Validate tags list format"""
    if not isinstance(value, list):
        raise ValidationError("Tags must be a list.")

    if len(value) > 20:
        raise ValidationError("Maximum 20 tags allowed.")

    for tag in value:
        if not isinstance(tag, str):
            raise ValidationError("All tags must be strings.")

        if len(tag) < 2:
            raise ValidationError("Tags must be at least 2 characters long.")

        if len(tag) > 50:
            raise ValidationError("Tags cannot exceed 50 characters.")

        if not re.match(r'^[a-zA-Z0-9\-_\s]+$', tag):
            raise ValidationError(f"Invalid tag format: {tag}. Only letters, numbers, hyphens, underscores, and spaces allowed.")


def validate_prompt_content(value):
    """Validate AI prompt content"""
    if not isinstance(value, str):
        raise ValidationError("Prompt must be a string.")

    if len(value) < 10:
        raise ValidationError("Prompt must be at least 10 characters long.")

    if len(value) > 4000:
        raise ValidationError("Prompt cannot exceed 4000 characters.")

    # Check for potentially harmful content
    harmful_patterns = [
        r'\b(nude|naked|sexual|explicit)\b',
        r'\b(violence|violent|kill|murder)\b',
        r'\b(hack|exploit|malware)\b',
    ]

    for pattern in harmful_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError("Prompt contains potentially harmful content.")


def validate_embedding_vector(value):
    """Validate embedding vector format"""
    if not isinstance(value, list):
        raise ValidationError("Embedding vector must be a list.")

    if len(value) not in [768, 1536, 3072]:  # Common embedding dimensions
        raise ValidationError("Embedding vector must be 768, 1536, or 3072 dimensions.")

    for i, val in enumerate(value):
        if not isinstance(val, (int, float)):
            raise ValidationError(f"Embedding vector value at position {i} must be a number.")

        if abs(val) > 10:  # Reasonable bounds for normalized embeddings
            raise ValidationError(f"Embedding vector value at position {i} is out of bounds: {val}")


def validate_metadata_structure(value):
    """Validate metadata JSON structure"""
    if not isinstance(value, dict):
        raise ValidationError("Metadata must be a JSON object (dictionary).")

    # Limit metadata size
    import json
    if len(json.dumps(value)) > 10000:  # 10KB limit
        raise ValidationError("Metadata size cannot exceed 10KB.")

    # Validate nested structure depth
    def check_depth(obj, depth=0, max_depth=5):
        if depth > max_depth:
            raise ValidationError("Metadata nesting too deep (max 5 levels).")

        if isinstance(obj, dict):
            for key, val in obj.items():
                if not isinstance(key, str):
                    raise ValidationError("All metadata keys must be strings.")
                check_depth(val, depth + 1, max_depth)
        elif isinstance(obj, list):
            for item in obj:
                check_depth(item, depth + 1, max_depth)

    check_depth(value)