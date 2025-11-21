import React, { useState } from "react";
import "./GridToolBar.css";

interface GridToolBarProps {
  enabled: boolean;
  gridContainerRef?: React.RefObject<HTMLDivElement>;
  onQuickSearchChange?: (value: string) => void;
  onDownloadClick?: () => void;
  onManualUpdateClick?: () => void;
  showFullscreenButton?: boolean;
  showDownloadButton?: boolean;
  showSearch?: boolean;
  showManualUpdateButton?: boolean;
  isMaximized?: boolean;
  onMaximizeToggle?: () => void;
}

const GridToolBar: React.FC<GridToolBarProps> = ({
  enabled,
  gridContainerRef,
  onQuickSearchChange,
  onDownloadClick,
  onManualUpdateClick,
  showFullscreenButton = true,
  showDownloadButton = true,
  showSearch = true,
  showManualUpdateButton = false,
  isMaximized = false,
  onMaximizeToggle,
}) => {
  const [searchValue, setSearchValue] = useState("");
  const [searchExpanded, setSearchExpanded] = useState(false);

  const handleQuickSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchValue(value);
    onQuickSearchChange?.(value);
  };

  if (!enabled) return null;

  return (
    <div className="grid-toolbar">
      {/* Search Input */}
      {showSearch && (
        <div
          className={`toolbar-search ${searchExpanded ? "expanded" : ""}`}
          onMouseEnter={() => setSearchExpanded(true)}
          onMouseLeave={() => {
            if (!searchValue) setSearchExpanded(false);
          }}
        >
          <button
            className="toolbar-button search-button"
            title="Search"
            onClick={() => setSearchExpanded(!searchExpanded)}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              width="12"
              height="12"
              fill="currentColor"
            >
              <path d="M10 2a8 8 0 105.293 14.293l4.707 4.707 1.414-1.414-4.707-4.707A8 8 0 0010 2zm0 2a6 6 0 110 12A6 6 0 0110 4z" />
            </svg>
          </button>
          <input
            type="text"
            value={searchValue}
            onChange={handleQuickSearchChange}
            placeholder="Search..."
            autoComplete="off"
            onFocus={() => setSearchExpanded(true)}
          />
        </div>
      )}

      {/* Download Button */}
      {showDownloadButton && (
        <button
          className="toolbar-button download-button"
          onClick={onDownloadClick}
          title="Download as CSV"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            width="12"
            height="12"
          >
            <path
              d="M6 21H18M12 3V17M12 17L17 12M12 17L7 12"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      )}

      {/* Maximize Button */}
      {showFullscreenButton && (
        <button
          className="toolbar-button maximize-button"
          onClick={onMaximizeToggle}
          title={isMaximized ? "Exit Fullscreen" : "Fullscreen"}
        >
          {isMaximized ? (
            // Compress icon (exit maximize)
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              width="12"
              height="12"
              fill="currentColor"
            >
              <path d="M8 3v2H4v4H2V3h6zm10 0h6v6h-2V5h-4V3zM8 21H2v-6h2v4h4v2zm10 0v-2h4v-4h2v6h-6z" />
            </svg>
          ) : (
            // Expand icon (enter maximize)
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              width="12"
              height="12"
              fill="currentColor"
            >
              <path d="M3 3h6v2H5v4H3V3zm12 0h6v6h-2V5h-4V3zm6 12v6h-6v-2h4v-4h2zm-12 6H3v-6h2v4h4v2z" />
            </svg>
          )}
        </button>
      )}

      {/* Manual Update Button */}
      {showManualUpdateButton && (
        <button
          className="toolbar-button update-button"
          onClick={onManualUpdateClick}
          title="Manual Update"
        >
          <svg
            viewBox="0 0 48 48"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            width="12"
            height="12"
          >
            <path
              d="M12.9998 8L6 14L12.9998 21"
              stroke="currentColor"
              strokeWidth="4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M6 14H28.9938C35.8768 14 41.7221 19.6204 41.9904 26.5C42.2739 33.7696 36.2671 40 28.9938 40H11.9984"
              stroke="currentColor"
              strokeWidth="4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      )}
    </div>
  );
};

export default GridToolBar;
