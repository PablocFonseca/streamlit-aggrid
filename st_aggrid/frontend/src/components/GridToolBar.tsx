import React, { useState } from "react";
import "./GridToolBar.css";

interface GridToolBarProps {
  enabled: boolean;
  onQuickSearchChange?: (value: string) => void; // Optional
  onDownloadClick?: () => void; // Optional
  onManualUpdateClick?: () => void; // Optional
  showFullscreenButton?: boolean;
  showDownloadButton?: boolean;
  showSearch?: boolean;
  showManualUpdateButton?: boolean; // New prop to enable/disable manual update button
}

const GridToolBar: React.FC<GridToolBarProps> = ({
  enabled,
  onQuickSearchChange,
  onDownloadClick,
  onManualUpdateClick,
  showFullscreenButton = true,
  showDownloadButton = true,
  showSearch = true,
  showManualUpdateButton = false,
}) => {
  const [searchValue, setSearchValue] = useState("");
  const [position, setPosition] = useState({ x: 10, y: 10 });
  const [collapsed, setCollapsed] = useState(false); // State to manage collapse

  const handleQuickSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchValue(value);
    onQuickSearchChange?.(value); // Call only if defined
  };

  const toggleCollapsed = () => {
    setCollapsed(!collapsed); // Toggle the collapsed state
  };

  if (!enabled) return null;

  return (
    <div
      className={`grid-toolbar ${collapsed ? "collapsed" : ""}`}
      style={{ top: position.y, right: collapsed ? 0 : position.x, left: "auto" }}
    >
      {/* Collapse/Expand Button */}
      <button
        className="toolbar-button toggle-button"
        onClick={toggleCollapsed}
        title={collapsed ? "Expand Toolbar" : "Collapse Toolbar"}
      >
        {collapsed ? (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            width="16"
            height="16"
            fill="currentColor"
          >
            <path d="M15.41 16.59L10.83 12l4.58-4.59L14 6l-6 6 6 6z" />
            <path d="M20.41 16.59L15.83 12l4.58-4.59L19 6l-6 6 6 6z" />
          </svg>
        ) : (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            width="16"
            height="16"
            fill="currentColor"
          >
            <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6z" />
            <path d="M3.59 16.59L8.17 12 3.59 7.41 5 6l6 6-6 6z" />
          </svg>
        )}
      </button>

      {/* Drag Handle */}
      {!collapsed && (
        <div
          className="drag-handle"
          title="Drag Toolbar"
          onMouseDown={(e) => {
            const toolbar = e.currentTarget.parentElement;
            const offsetX = e.clientX - toolbar!.getBoundingClientRect().left;
            const offsetY = e.clientY - toolbar!.getBoundingClientRect().top;

            const handleMouseMove = (moveEvent: MouseEvent) => {
              setPosition({
                x: window.innerWidth - moveEvent.clientX - (toolbar!.offsetWidth - offsetX),
                y: moveEvent.clientY - offsetY,
              });
            };

            const handleMouseUp = () => {
              document.removeEventListener("mousemove", handleMouseMove);
              document.removeEventListener("mouseup", handleMouseUp);
            };

            document.addEventListener("mousemove", handleMouseMove);
            document.addEventListener("mouseup", handleMouseUp);
          }}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            width="16"
            height="16"
            fill="#D3D3D3"
          >
            <path d="M7 2a2 2 0 10.001 4.001A2 2 0 007 2zm0 6a2 2 0 10.001 4.001A2 2 0 007 8zm0 6a2 2 0 10.001 4.001A2 2 0 007 14zm6-8a2 2 0 10-.001-4.001A2 2 0 0013 6zm0 2a2 2 0 10.001 4.001A2 2 0 0013 8zm0 6a2 2 0 10.001 4.001A2 2 0 0013 14z" />
          </svg>
        </div>
      )}

      {/* Manual Update Button */}
      {showManualUpdateButton && !collapsed && (
        <button
          className="toolbar-button update-button"
          onClick={onManualUpdateClick}
          title="Manual Update"
        >
          <svg
            viewBox="0 0 48 48"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M12.9998 8L6 14L12.9998 21"
              stroke="#000000"
              stroke-width="4"
              stroke-linecap="round"
              stroke-linejoin="round"
            ></path>
            <path
              d="M6 14H28.9938C35.8768 14 41.7221 19.6204 41.9904 26.5C42.2739 33.7696 36.2671 40 28.9938 40H11.9984"
              stroke="#000000"
              stroke-width="4"
              stroke-linecap="round"
              stroke-linejoin="round"
            ></path>
          </svg>
        </button>
      )}

      {/* Fullscreen Button */}
      {showFullscreenButton && !collapsed && (
        <button
          className="toolbar-button fullscreen-button"
          onClick={() => {
            const gridContainer = document.getElementById("gridContainer");
            if (!document.fullscreenElement) {
              gridContainer?.requestFullscreen();
            } else {
              document.exitFullscreen();
            }
          }}
          title="Toggle Fullscreen View"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            width="16"
            height="16"
            fill="currentColor"
          >
            <path d="M3 3h6v2H5v4H3V3zm12 0h6v6h-2V5h-4V3zm6 12v6h-6v-2h4v-4h2zm-12 6H3v-6h2v4h4v2z" />
          </svg>
        </button>
      )}

      {/* Download Button */}
      {showDownloadButton && !collapsed && (
        <button
          className="toolbar-button download-button"
          onClick={onDownloadClick}
          title="Download as CSV"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M6 21H18M12 3V17M12 17L17 12M12 17L7 12"
              stroke="#000000"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            ></path>
          </svg>
        </button>
      )}

      {/* Search Input */}
      {showSearch && !collapsed && (
        <div className="toolbar-search">
          <div className="toolbar-input">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              width="16"
              height="16"
              fill="currentColor"
            >
              <path d="M10 2a8 8 0 105.293 14.293l4.707 4.707 1.414-1.414-4.707-4.707A8 8 0 0010 2zm0 2a6 6 0 110 12A6 6 0 0110 4z" />
            </svg>
            <input
              type="text"
              value={searchValue}
              onChange={handleQuickSearchChange}
              placeholder="Search..."
              title="Quick Search"
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default GridToolBar;
