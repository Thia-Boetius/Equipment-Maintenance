/**
 * Request validation middleware.
 * Usage: validate(schema) where schema is an object of
 * { field: { type, required, min, max } }
 */
function validate(schema) {
    return (req, res, next) => {
        const errors = [];
        const data   = req.body;

        for (const [field, rules] of Object.entries(schema)) {
            const value = data[field];

            if (rules.required && (value === undefined || value === null || value === '')) {
                errors.push(`${field} is required`);
                continue;
            }

            if (value !== undefined && value !== null && value !== '') {
                if (rules.type === 'number' && isNaN(Number(value))) {
                    errors.push(`${field} must be a number`);
                }
                if (rules.type === 'string' && typeof value !== 'string') {
                    errors.push(`${field} must be a string`);
                }
                if (rules.type === 'date' && isNaN(Date.parse(value))) {
                    errors.push(`${field} must be a valid date`);
                }
                if (rules.min !== undefined && Number(value) < rules.min) {
                    errors.push(`${field} must be at least ${rules.min}`);
                }
                if (rules.max !== undefined && Number(value) > rules.max) {
                    errors.push(`${field} must be at most ${rules.max}`);
                }
                if (rules.maxLength && String(value).length > rules.maxLength) {
                    errors.push(`${field} must be at most ${rules.maxLength} characters`);
                }
            }
        }

        if (errors.length > 0) {
            return res.status(400).json({ error: 'Validation failed', details: errors });
        }

        next();
    };
}

module.exports = { validate };
