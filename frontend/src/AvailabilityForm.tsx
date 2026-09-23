import { useState } from 'react';

type Result = {
  room_name: string;
  available: boolean;
  capacity: number;
  price_per_night: number;
  nights: number;
  estimated_total: number;
  reason?: string | null;
};

type AvailabilityFormProps = {
  call: (path: string, opts?: RequestInit) => Promise<any>;
};

export function AvailabilityForm({ call }: AvailabilityFormProps) {
  const [checkIn, setCheckIn] = useState('');
  const [checkOut, setCheckOut] = useState('');
  const [guests, setGuests] = useState('2');
  const [results, setResults] = useState<Result[]>([]);
  const [error, setError] = useState('');
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const today = new Date().toISOString().split('T')[0];

  const search = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setResults([]);

    if (!checkIn || !checkOut) {
      setError('Please select both check-in and check-out dates.');
      return;
    }

    if (checkOut <= checkIn) {
      setError('Check-out must be after check-in.');
      return;
    }

    const guestCount = Number(guests);

    if (!Number.isInteger(guestCount) || guestCount < 1 || guestCount > 20) {
      setError('Guests must be between 1 and 20.');
      return;
    }

    setLoading(true);

    try {
      const data = await call('/availability/search', {
        method: 'POST',
        body: JSON.stringify({
          check_in: checkIn,
          check_out: checkOut,
          guests: guestCount,
        }),
      });

      setResults(Array.isArray(data) ? data : []);
    } catch (e: any) {
      setError(e?.message || 'Unable to check availability. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const toggleAvailability = () => {
    setOpen((current) => !current);
    setError('');
  };

  return (
    <section className="availability-box" aria-label="Hotel availability search">
      <button
        type="button"
        className={`availability-toggle ${open ? 'is-open' : ''}`}
        onClick={toggleAvailability}
        aria-expanded={open}
        aria-controls="availability-panel"
      >
        <span>{open ? 'Hide availability search' : 'Check demo availability'}</span>
        <span className="availability-toggle-icon" aria-hidden="true">
          {open ? '−' : '+'}
        </span>
      </button>

      {open && (
        <div
          id="availability-panel"
          className="availability-panel"
        >
          <div className="availability-heading">
            <div>
              <p className="availability-eyebrow">AURELIA HOTEL</p>
              <h3>Find your ideal stay</h3>
              <p>
                Select your dates and the number of guests to explore
                demo room availability.
              </p>
            </div>
          </div>

          <form
            className="availability-form"
            onSubmit={search}
          >
            <div className="availability-field">
              <label htmlFor="check-in">
                Check-in
              </label>

              <input
                id="check-in"
                name="check-in"
                required
                type="date"
                min={today}
                value={checkIn}
                onChange={(event) => {
                  setCheckIn(event.target.value);

                  if (checkOut && event.target.value >= checkOut) {
                    setCheckOut('');
                  }
                }}
              />
            </div>

            <div className="availability-field">
              <label htmlFor="check-out">
                Check-out
              </label>

              <input
                id="check-out"
                name="check-out"
                required
                type="date"
                min={checkIn || today}
                value={checkOut}
                onChange={(event) => setCheckOut(event.target.value)}
              />
            </div>

            <div className="availability-field">
              <label htmlFor="guest-count">
                Guests
              </label>

              <input
                id="guest-count"
                name="guests"
                required
                type="number"
                min="1"
                max="20"
                step="1"
                value={guests}
                onChange={(event) => setGuests(event.target.value)}
              />
            </div>

            <button
              type="submit"
              className="availability-search-button"
              disabled={loading}
            >
              {loading ? 'Checking...' : 'Search availability'}
            </button>
          </form>

          {error && (
            <p
              className="availability-error"
              role="alert"
            >
              {error}
            </p>
          )}

          {results.length > 0 && (
            <div
              className="availability-results"
              aria-live="polite"
            >
              <div className="availability-results-header">
                <h4>Available rooms</h4>
                <span>{results.length} result(s)</span>
              </div>

              {results.map((room) => (
                <article
                  className="availability-result"
                  key={`${room.room_name}-${room.capacity}`}
                >
                  <div className="availability-result-info">
                    <div className="availability-result-title">
                      <h4>{room.room_name}</h4>

                      <span
                        className={
                          room.available
                            ? 'availability-status available'
                            : 'availability-status unavailable'
                        }
                      >
                        {room.available ? 'Available' : 'Unavailable'}
                      </span>
                    </div>

                    <p>
                      {room.available
                        ? `${room.nights} night(s) · Capacity: ${room.capacity} guests`
                        : room.reason || 'This room is unavailable for the selected dates.'}
                    </p>

                    {room.available && (
                      <small>
                        ${room.price_per_night} per night
                      </small>
                    )}
                  </div>

                  <div className="availability-result-price">
                    <strong>
                      ${Number(room.estimated_total).toLocaleString()}
                    </strong>

                    <span>Estimated total</span>
                  </div>
                </article>
              ))}
            </div>
          )}

          <p className="availability-note">
            Demo information only. No reservation is created.
          </p>
        </div>
      )}
    </section>
  );
}